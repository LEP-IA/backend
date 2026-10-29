import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from app import models, schemas

DURACOES_VALIDAS = (7, 14)

# O cliente pode mandar o início da sprint alinhado à meia-noite local do dono
# (assim as sprints trocam de número na virada do dia dele). Projetos já
# andamento (ex.: sprints de setembro/outubro) precisam registrar a data real.
TOLERANCIA_INICIO_FUTURO = timedelta(minutes=5)


class SprintError(ValueError):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _com_timezone(valor: datetime) -> datetime:
    """Garante datetime com timezone (o banco pode devolver naive em UTC)."""
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


def sprint_ativa(board: models.Board) -> bool:
    return board.sprint_inicio is not None and board.sprint_encerrada_em is None


def numero_sprint(inicio: datetime, duracao_dias: int, momento: datetime) -> int:
    """Sprint em que `momento` cai: 1 nos primeiros N dias, 2 nos N seguintes..."""
    decorrido = max(momento - inicio, timedelta(0))
    return int(decorrido / timedelta(days=duracao_dias)) + 1


def total_sprints(inicio: datetime, duracao_dias: int, fim: datetime) -> int:
    """Quantas sprints (mesmo que incompletas) o projeto durou até `fim`."""
    decorrido = max(fim - inicio, timedelta(0))
    return max(1, math.ceil(decorrido / timedelta(days=duracao_dias)))


def montar_sprint_out(board: models.Board) -> schemas.SprintOut:
    if board.sprint_inicio is None:
        return schemas.SprintOut()

    inicio = _com_timezone(board.sprint_inicio)
    duracao = board.sprint_duracao_dias
    encerrada_em = (
        _com_timezone(board.sprint_encerrada_em)
        if board.sprint_encerrada_em
        else None
    )

    if encerrada_em:
        return schemas.SprintOut(
            ativa=False,
            duracao_dias=duracao,
            inicio=inicio,
            encerrada_em=encerrada_em,
            total_sprints=board.sprint_total,
        )

    numero = numero_sprint(inicio, duracao, _agora())
    periodo_inicio = inicio + timedelta(days=duracao * (numero - 1))
    return schemas.SprintOut(
        ativa=True,
        duracao_dias=duracao,
        inicio=inicio,
        numero_atual=numero,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_inicio + timedelta(days=duracao),
    )


def iniciar_sprint(
    board: models.Board, duracao_dias: int, inicio: Optional[datetime] = None
) -> None:
    if sprint_ativa(board):
        raise SprintError("Já existe uma sprint ativa neste board")
    if duracao_dias not in DURACOES_VALIDAS:
        raise SprintError("A duração da sprint deve ser de 7 ou 14 dias", 422)

    agora = _agora()
    if inicio is None:
        inicio = agora
    else:
        if inicio.tzinfo is None:
            raise SprintError("O início da sprint precisa informar o fuso horário", 422)
        inicio = inicio.astimezone(timezone.utc)
        if inicio > agora + TOLERANCIA_INICIO_FUTURO:
            raise SprintError("Início da sprint inválido", 422)

    board.sprint_duracao_dias = duracao_dias
    board.sprint_inicio = inicio
    board.sprint_encerrada_em = None
    board.sprint_total = None


def encerrar_sprint(board: models.Board, fim: Optional[datetime] = None) -> None:
    if not sprint_ativa(board):
        raise SprintError("Não há sprint ativa neste board")

    agora = _agora()
    if fim is None:
        fim = agora
    else:
        if fim.tzinfo is None:
            raise SprintError("O encerramento precisa informar o fuso horário", 422)
        fim = fim.astimezone(timezone.utc)
        inicio = _com_timezone(board.sprint_inicio)
        if fim < inicio:
            raise SprintError("O encerramento não pode ser antes do início", 422)
        if fim > agora + TOLERANCIA_INICIO_FUTURO:
            raise SprintError("Encerramento inválido", 422)

    board.sprint_encerrada_em = fim
    board.sprint_total = total_sprints(
        _com_timezone(board.sprint_inicio), board.sprint_duracao_dias, fim
    )
