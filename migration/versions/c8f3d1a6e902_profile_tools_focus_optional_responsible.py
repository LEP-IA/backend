"""profile technologies/focos and optional task responsible

Revision ID: c8f3d1a6e902
Revises: b2d8f5c1a014
Create Date: 2026-10-23 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f3d1a6e902"
down_revision: Union[str, Sequence[str], None] = "b2d8f5c1a014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "perfil_profissional",
        sa.Column("technologies", sa.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "perfil_profissional",
        sa.Column("focos", sa.ARRAY(sa.String()), nullable=True),
    )
    op.alter_column(
        "tarefa",
        "responsavel_email",
        existing_type=sa.String(),
        nullable=True,
    )
    op.add_column(
        "tarefa",
        sa.Column("focos", sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tarefa", "focos")
    op.alter_column(
        "tarefa",
        "responsavel_email",
        existing_type=sa.String(),
        nullable=False,
    )
    op.drop_column("perfil_profissional", "focos")
    op.drop_column("perfil_profissional", "technologies")
