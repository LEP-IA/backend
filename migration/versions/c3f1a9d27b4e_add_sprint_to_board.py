"""add sprint to board

Revision ID: c3f1a9d27b4e
Revises: 820d7c1eb3de
Create Date: 2026-10-22 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f1a9d27b4e'
down_revision: Union[str, Sequence[str], None] = '820d7c1eb3de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("board", sa.Column("sprint_duracao_dias", sa.Integer(), nullable=True))
    op.add_column(
        "board", sa.Column("sprint_inicio", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "board",
        sa.Column("sprint_encerrada_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("board", sa.Column("sprint_total", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_board_sprint_duracao_dias",
        "board",
        "sprint_duracao_dias IS NULL OR sprint_duracao_dias IN (7, 14)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_board_sprint_duracao_dias", "board", type_="check")
    op.drop_column("board", "sprint_total")
    op.drop_column("board", "sprint_encerrada_em")
    op.drop_column("board", "sprint_inicio")
    op.drop_column("board", "sprint_duracao_dias")
