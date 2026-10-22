from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app import models

# O "dia" da tarefa é o dia no horário de Brasília (UTC-3, sem horário de verão).
FUSO_DIAS = timezone(timedelta(hours=-3))

# Colunas com regra especial (mesmos valores de Tarefa.status usados no kanban)
STATUS_BACKLOG = "BACKLOG"
STATUS_CONCLUIDO = "DONE"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _com_timezone(valor: datetime) -> datetime:
    """Garante datetime com timezone (o banco pode devolver naive em UTC)."""
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


def _dia(momento: datetime) -> date:
    return _com_timezone(momento).astimezone(FUSO_DIAS).date()


def _passagem_aberta(
    tarefa: models.Tarefa,
) -> Optional[models.TarefaColunaHistorico]:
    for passagem in tarefa.historico_colunas:
        if passagem.saiu_em is None:
            return passagem
    return None


def registrar_mudanca_status(
    db: Session, tarefa: models.Tarefa, novo_status: str
) -> None:
    """Fecha a passagem atual e abre a da nova coluna.

    Deve ser chamada quando a tarefa é criada (com `tarefa.status` já definido
    e a tarefa já presente na sessão) e sempre que o status muda. Não faz commit.
    Se o status não mudou, não faz nada.
    """
    agora = _agora()
    aberta = _passagem_aberta(tarefa)

    if aberta is not None:
        if aberta.status == novo_status:
            return
        aberta.saiu_em = agora
        # Garante o UPDATE (fechar a antiga) antes do INSERT da nova, por causa
        # do índice único de uma passagem aberta por tarefa.
        db.flush()

    tarefa.historico_colunas.append(
        models.TarefaColunaHistorico(status=novo_status, entrou_em=agora)
    )


def _eh_backlog(status: str) -> bool:
    return status.upper() == STATUS_BACKLOG


def _eh_concluido(status: str) -> bool:
    return status.upper() == STATUS_CONCLUIDO


def _dias_da_passagem(passagem: models.TarefaColunaHistorico, agora: datetime) -> set[date]:
    """Dias de calendário (inclusive) em que a tarefa esteve nessa passagem.

    Na coluna de concluído o tempo fica congelado: conta só o dia em que a
    tarefa foi concluída, por mais tempo que ela fique lá.
    """
    inicio = _dia(passagem.entrou_em)
    if _eh_concluido(passagem.status):
        return {inicio}
    fim = _dia(passagem.saiu_em or agora)
    return {inicio + timedelta(days=i) for i in range((fim - inicio).days + 1)}


def dias_por_coluna(
    tarefa: models.Tarefa, agora: Optional[datetime] = None
) -> dict[str, int]:
    """Quantos dias a tarefa ficou em cada coluna.

    Conta os dias de calendário em que a tarefa esteve na coluna: a cada novo
    dia que passa na coluna soma 1. Se a tarefa sai e volta para a mesma coluna,
    cada dia é contado só uma vez. Em concluído o tempo é congelado.
    """
    agora = agora or _agora()
    dias: dict[str, set[date]] = {}

    for passagem in tarefa.historico_colunas:
        dias.setdefault(passagem.status, set()).update(
            _dias_da_passagem(passagem, agora)
        )

    return {status: len(conjunto) for status, conjunto in dias.items()}


def dias_de_duracao(
    tarefa: models.Tarefa, agora: Optional[datetime] = None
) -> int:
    """Duração da tarefa em dias.

    Começa a contar quando a tarefa sai do backlog e congela quando ela chega em
    concluído: criada em andamento hoje e concluída amanhã = 2 dias. Enquanto
    estiver no backlog a duração é 0. Se a tarefa for reaberta (sair de
    concluído), a contagem volta a andar e congela de novo ao concluir.
    """
    agora = agora or _agora()
    dias: set[date] = set()

    for passagem in tarefa.historico_colunas:
        if not _eh_backlog(passagem.status):
            dias.update(_dias_da_passagem(passagem, agora))

    return len(dias)
