"""add tarefa coluna historico

Revision ID: d4a7e2b91c05
Revises: c3f1a9d27b4e
Create Date: 2026-10-22 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a7e2b91c05'
down_revision: Union[str, Sequence[str], None] = 'c3f1a9d27b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tarefa_coluna_historico",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tarefa_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("entrou_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("saiu_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tarefa_id"], ["tarefa.id_tarefa"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tarefa_coluna_historico_id"), "tarefa_coluna_historico", ["id"]
    )
    op.create_index(
        op.f("ix_tarefa_coluna_historico_tarefa_id"),
        "tarefa_coluna_historico",
        ["tarefa_id"],
    )
    # No máximo uma passagem aberta (sem saída) por tarefa
    op.create_index(
        "uq_tarefa_coluna_aberta",
        "tarefa_coluna_historico",
        ["tarefa_id"],
        unique=True,
        postgresql_where=sa.text("saiu_em IS NULL"),
    )

    # Tarefas que já existem começam a ser contadas a partir de agora,
    # na coluna em que estão (não dá para saber quando entraram nela).
    op.execute(
        """
        INSERT INTO tarefa_coluna_historico (tarefa_id, status, entrou_em)
        SELECT id_tarefa, status, now() FROM tarefa
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_tarefa_coluna_aberta", table_name="tarefa_coluna_historico")
    op.drop_index(
        op.f("ix_tarefa_coluna_historico_tarefa_id"),
        table_name="tarefa_coluna_historico",
    )
    op.drop_index(
        op.f("ix_tarefa_coluna_historico_id"), table_name="tarefa_coluna_historico"
    )
    op.drop_table("tarefa_coluna_historico")
