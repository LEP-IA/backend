"""add previsao prazo to tarefa

Revision ID: e5b8c3a1f206
Revises: d4a7e2b91c05
Create Date: 2026-10-22 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5b8c3a1f206'
down_revision: Union[str, Sequence[str], None] = 'd4a7e2b91c05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tarefa", sa.Column("previsao_dias", sa.Float(), nullable=True))
    op.add_column(
        "tarefa", sa.Column("previsao_esforco_horas", sa.Float(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tarefa", "previsao_esforco_horas")
    op.drop_column("tarefa", "previsao_dias")
