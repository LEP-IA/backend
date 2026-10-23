"""Previsão de prazo da tarefa usando o serviço `prazo_model`.

O modelo recebe parâmetros do profissional responsável (área e horas semanais
dedicadas ao board) e da tarefa (complexidade e prioridade). Também recebe o
`tarefa_id` e o `usuario_id`: eles não entram no cálculo, só voltam na resposta
para garantir que a previsão gravada é mesmo da tarefa que a pediu.

Falha do modelo (fora do ar, timeout, resposta inválida) nunca impede salvar a
tarefa: a previsão simplesmente fica vazia e é tentada de novo na próxima edição.
"""

import logging
import math
import unicodedata
from datetime import date, datetime, time, timedelta
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app import models
from app.config import PRAZO_MODEL_TIMEOUT, PRAZO_MODEL_URL
from app.services import task_time_service

logger = logging.getLogger(__name__)

# Valor do campo `area` salvo no perfil profissional -> nome aceito pelo modelo.
AREAS_DO_MODELO = {
    "technology": "Tecnologia e Desenvolvimento",
    "design": "Design",
    "product": "Produto",
    "management": "Gestão e Administração",
    "engineering": "Engenharia",
    "marketing": "Marketing e Comunicação",
    "education": "Educação",
    "health": "Saúde",
    "finance": "Finanças e Contabilidade",
    "hr": "Recursos Humanos",
    "research": "Pesquisa e Inovação",
    "other": "Outro",
}
AREA_PADRAO = "Outro"

# Complexidade/prioridade da tarefa (baixo|médio|alto, com variações) -> modelo.
NIVEIS_DO_MODELO = {
    "baixo": "Baixa",
    "baixa": "Baixa",
    "medio": "Média",
    "media": "Média",
    "alto": "Alta",
    "alta": "Alta",
}
# A complexidade só é definida depois da análise da IA; sem ela usa o nível médio.
COMPLEXIDADE_PADRAO = "Média"
PRIORIDADE_PADRAO = "Média"


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def _normalizar_area(area: Optional[str]) -> str:
    """Perfil guarda o código (ex: 'technology') ou um texto livre quando 'Outro'."""
    if not area:
        return AREA_PADRAO
    chave = area.strip().lower()
    if chave in AREAS_DO_MODELO:
        return AREAS_DO_MODELO[chave]
    # Aceita também o nome já no formato do modelo
    for nome in AREAS_DO_MODELO.values():
        if chave == nome.lower():
            return nome
    return AREA_PADRAO


def _normalizar_nivel(valor: Optional[str], padrao: str) -> str:
    if not valor:
        return padrao
    return NIVEIS_DO_MODELO.get(_sem_acento(valor.strip().lower()), padrao)


def montar_entrada(db: Session, tarefa: models.Tarefa) -> Optional[dict]:
    """Monta o corpo enviado ao modelo.

    Retorna None quando falta algum dado indispensável: sem as horas semanais
    do responsável no board não há como calcular o prazo.
    """
    if not tarefa.responsavel_email:
        return None

    membro = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == tarefa.id_board,
            models.BoardMembro.usuario_email == tarefa.responsavel_email,
        )
        .first()
    )
    horas_semanais = membro.weekly_hours if membro else None
    if not horas_semanais or horas_semanais <= 0:
        return None

    perfil = (
        db.query(models.PerfilProfissional)
        .filter(models.PerfilProfissional.usuario_email == tarefa.responsavel_email)
        .first()
    )

    return {
        "tarefa_id": str(tarefa.id_tarefa),
        "usuario_id": tarefa.responsavel_email,
        "area": _normalizar_area(perfil.area if perfil else None),
        "horas_semanais": horas_semanais,
        "complexidade": _normalizar_nivel(tarefa.complexity, COMPLEXIDADE_PADRAO),
        "prioridade": _normalizar_nivel(tarefa.prioridade, PRIORIDADE_PADRAO),
    }


def _consultar_modelo(entrada: dict) -> Optional[dict]:
    """Chama o modelo e confere se a resposta é da mesma tarefa."""
    try:
        resposta = requests.post(
            f"{PRAZO_MODEL_URL.rstrip('/')}/estimar-prazo",
            json=entrada,
            timeout=PRAZO_MODEL_TIMEOUT,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError) as erro:
        logger.warning(
            "Prazo model indisponível para a tarefa %s: %s", entrada["tarefa_id"], erro
        )
        return None

    # Sincronização: só aceita a previsão se ela veio identificada com a tarefa
    if str(dados.get("tarefa_id")) != entrada["tarefa_id"]:
        logger.error(
            "Prazo model devolveu a tarefa %r para o pedido da tarefa %s; descartado",
            dados.get("tarefa_id"),
            entrada["tarefa_id"],
        )
        return None

    try:
        return {
            "prazo_dias": float(dados["prazo_dias"]),
            "esforco_horas": float(dados["esforco_horas"]),
        }
    except (KeyError, TypeError, ValueError):
        logger.error("Resposta inesperada do prazo model: %r", dados)
        return None


def atualizar_previsao(db: Session, tarefa: models.Tarefa) -> bool:
    """Calcula a previsão da tarefa e grava em `tarefa` (sem commit).

    Retorna True se a previsão foi atualizada. Em qualquer falha mantém o que
    já existia e retorna False.
    """
    if not PRAZO_MODEL_URL:
        return False

    entrada = montar_entrada(db, tarefa)
    if entrada is None:
        return False

    resultado = _consultar_modelo(entrada)
    if resultado is None:
        return False

    tarefa.previsao_dias = resultado["prazo_dias"]
    tarefa.previsao_esforco_horas = resultado["esforco_horas"]
    _definir_datas(tarefa)
    return True


def ultimo_dia_util(inicio: date, dias_uteis: int) -> date:
    """Dia em que se completa o `dias_uteis`-ésimo dia útil contando de `inicio`.

    O próprio dia de início conta como o dia 1 se for dia útil (1 dia útil termina
    no mesmo dia, como na contagem de dias da tarefa). Sábado e domingo não contam;
    feriados não são considerados.
    """
    dia = inicio
    contados = 0
    while True:
        if dia.weekday() < 5:
            contados += 1
            if contados >= dias_uteis:
                return dia
        dia += timedelta(days=1)


def recalcular_datas(tarefa: models.Tarefa) -> bool:
    """Refaz a data de fim com a previsão já salva (ex: o início foi alterado)."""
    if tarefa.previsao_dias is None:
        return False
    _definir_datas(tarefa)
    return True


def _definir_datas(tarefa: models.Tarefa) -> None:
    """Data de fim a partir do início informado e da previsão.

    O início é o informado na tarefa (se não houver, usa o dia da criação); o fim
    é o último dia útil do prazo previsto, contado a partir do início.
    """
    inicio = (
        tarefa.data_inicio.date()
        if tarefa.data_inicio
        else task_time_service.dia_de_criacao(tarefa)
    )
    dias = max(1, math.ceil(tarefa.previsao_dias))
    fim = ultimo_dia_util(inicio, dias)
    tarefa.data_inicio = datetime.combine(inicio, time.min)
    tarefa.data_fim = datetime.combine(fim, time.min)
