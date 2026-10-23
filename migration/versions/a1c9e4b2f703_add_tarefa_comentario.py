"""add tarefa comentario

Revision ID: a1c9e4b2f703
Revises: e5b8c3a1f206
Create Date: 2026-10-22 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c9e4b2f703"
down_revision: Union[str, Sequence[str], None] = "e5b8c3a1f206"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tarefa_comentario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tarefa_id", sa.Integer(), nullable=False),
        sa.Column("autor_email", sa.String(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tarefa_id"], ["tarefa.id_tarefa"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_email"], ["usuario.email"]),
    )
    op.create_index(
        "ix_tarefa_comentario_id", "tarefa_comentario", ["id"], unique=False
    )
    op.create_index(
        "ix_tarefa_comentario_tarefa_id",
        "tarefa_comentario",
        ["tarefa_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tarefa_comentario_tarefa_id", table_name="tarefa_comentario")
    op.drop_index("ix_tarefa_comentario_id", table_name="tarefa_comentario")
    op.drop_table("tarefa_comentario")
