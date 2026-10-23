"""Sugestão de executor: monta os membros do board e consulta o prazo_model."""

from __future__ import annotations

import logging
import unicodedata

import requests
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.config import PRAZO_MODEL_TIMEOUT, PRAZO_MODEL_URL

logger = logging.getLogger(__name__)

PESO_ALTA = 4.0
PESO_MEDIA = 2.0
PESO_BAIXA = 1.0
MIN_SUGESTOES = 2
MAX_SUGESTOES = 3
FOCO_PREFIX = "#foco:"


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def _chave(valor: str | None) -> str:
    if not valor:
        return ""
    return " ".join(_sem_acento(str(valor)).strip().lower().split())


def _prioridade(valor: str | None) -> str:
    chave = _chave(valor)
    if chave in {"alto", "alta"}:
        return "alta"
    if chave in {"medio", "media"}:
        return "media"
    if chave in {"baixo", "baixa"}:
        return "baixa"
    return ""


def _listas_da_tarefa(tarefa: models.Tarefa) -> tuple[list[str], list[str]]:
    focos = [item for item in (tarefa.focos or []) if item]
    techs: list[str] = []
    for item in tarefa.technologies or []:
        if not item:
            continue
        if str(item).startswith(FOCO_PREFIX):
            focos.append(str(item)[len(FOCO_PREFIX) :])
        else:
            techs.append(str(item))
    return techs, focos


def _contagem(tarefas: list[models.Tarefa], email: str, ignorar_id: int) -> dict[str, int]:
    alta = media = baixa = abertas = 0
    for tarefa in tarefas:
        if tarefa.id_tarefa == ignorar_id:
            continue
        if (tarefa.status or "").upper() == "DONE":
            continue
        if _chave(tarefa.responsavel_email) != _chave(email):
            continue
        abertas += 1
        nivel = _prioridade(tarefa.prioridade)
        if nivel == "alta":
            alta += 1
        elif nivel == "media":
            media += 1
        else:
            baixa += 1
    return {
        "tarefas_abertas": abertas,
        "tarefas_alta": alta,
        "tarefas_media": media,
        "tarefas_baixa": baixa,
    }


def _montar_candidatos(db: Session, tarefa: models.Tarefa) -> list[dict]:
    membros = (
        db.query(models.BoardMembro)
        .options(selectinload(models.BoardMembro.usuario))
        .filter(models.BoardMembro.board_id == tarefa.id_board)
        .all()
    )
    tarefas = (
        db.query(models.Tarefa)
        .filter(models.Tarefa.id_board == tarefa.id_board)
        .all()
    )
    emails = [membro.usuario_email for membro in membros if membro.usuario_email]
    perfis = {
        perfil.usuario_email: perfil
        for perfil in db.query(models.PerfilProfissional)
        .filter(models.PerfilProfissional.usuario_email.in_(emails))
        .all()
    } if emails else {}

    candidatos = []
    for membro in membros:
        email = (membro.usuario_email or "").strip()
        if not email:
            continue
        perfil = perfis.get(email)
        usuario = membro.usuario
        candidatos.append({
            "usuario_id": email,
            "nome": usuario.nome if usuario else email,
            "specialization": perfil.specialization if perfil else None,
            "focos": list(perfil.focos or []) if perfil else [],
            "technologies": list(perfil.technologies or []) if perfil else [],
            "seniority": perfil.seniority if perfil else None,
            "experience_time": perfil.experience_time if perfil else None,
            **_contagem(tarefas, email, tarefa.id_tarefa),
        })
    return candidatos


def _ranquear_local(candidatos: list[dict], focos: list[str], techs: list[str]) -> list[dict]:
    focos_n = [_chave(item) for item in focos if _chave(item)]
    techs_n = [_chave(item) for item in techs if _chave(item)]
    ranqueados = []
    for candidato in candidatos:
        carga = (
            candidato["tarefas_alta"] * PESO_ALTA
            + candidato["tarefas_media"] * PESO_MEDIA
            + candidato["tarefas_baixa"] * PESO_BAIXA
        )
        disponibilidade = 1.0 - (carga / (carga + 4.0))
        menos_tarefas = 1.0 - (candidato["tarefas_abertas"] / (candidato["tarefas_abertas"] + 3.0))
        perfil_foco = {_chave(item) for item in candidato.get("focos") or []}
        especializacao = _chave(candidato.get("specialization"))
        if especializacao:
            perfil_foco.add(especializacao)
        foco = any(
            item in perfil_foco or (especializacao and (item in especializacao or especializacao in item))
            for item in focos_n
        )
        intersecao = len(set(techs_n) & {_chave(item) for item in candidato.get("technologies") or []})
        tech = (intersecao / len(techs_n)) if techs_n else 0.45
        score = 0.26 * menos_tarefas + 0.22 * disponibilidade + 0.22 * (1.0 if foco else 0.0) + 0.16 * tech
        ranqueados.append((round(score, 4), candidato, foco, intersecao))
    ranqueados.sort(key=lambda item: (-item[0], item[1]["tarefas_alta"], item[1]["tarefas_abertas"]))
    limite = min(MAX_SUGESTOES, max(MIN_SUGESTOES, len(ranqueados))) if ranqueados else 0
    if len(ranqueados) < MIN_SUGESTOES:
        limite = len(ranqueados)
    sugestoes = []
    for score, candidato, foco, intersecao in ranqueados[:limite]:
        motivos = []
        if candidato["tarefas_abertas"] == 0:
            motivos.append("Sem tarefas em aberto neste board")
        if candidato["tarefas_alta"] == 0:
            motivos.append("Nenhuma tarefa de alta prioridade")
        if foco:
            motivos.append("Foco da tarefa combina com a especialização")
        if intersecao and techs_n:
            motivos.append(f"{intersecao} de {len(techs_n)} ferramentas em comum")
        sugestoes.append({
            "usuario_id": candidato["usuario_id"],
            "nome": candidato["nome"],
            "score": score,
            "motivos": motivos[:4],
        })
    return sugestoes


def _consultar_modelo(payload: dict) -> list[dict] | None:
    if not PRAZO_MODEL_URL:
        return None
    try:
        resposta = requests.post(
            f"{PRAZO_MODEL_URL.rstrip('/')}/sugerir-executor",
            json=payload,
            timeout=max(PRAZO_MODEL_TIMEOUT, 8),
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError) as erro:
        logger.warning("Sugestão de executor indisponível: %s", erro)
        return None
    sugestoes = dados.get("sugestoes")
    return sugestoes if isinstance(sugestoes, list) else None


def sugerir_executores(db: Session, task_id: int) -> schemas.ExecutorSuggestionListOut | None:
    tarefa = db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == task_id).first()
    if not tarefa:
        return None

    candidatos = _montar_candidatos(db, tarefa)
    techs, focos = _listas_da_tarefa(tarefa)
    payload = {
        "tarefa_id": str(tarefa.id_tarefa),
        "focos": focos,
        "technologies": techs,
        "complexidade": tarefa.complexity,
        "prioridade": tarefa.prioridade,
        "candidatos": candidatos,
    }
    sugestoes = _consultar_modelo(payload) or _ranquear_local(candidatos, focos, techs)

    saida = []
    for item in sugestoes:
        email = str(item.get("usuario_id") or "").strip()
        if not email:
            continue
        saida.append(
            schemas.ExecutorSuggestionOut(
                responsibleId=email,
                name=str(item.get("nome") or email),
                email=email,
                score=float(item.get("score") or 0),
                reasons=[str(motivo) for motivo in (item.get("motivos") or []) if motivo],
            )
        )
    return schemas.ExecutorSuggestionListOut(suggestions=saida)
