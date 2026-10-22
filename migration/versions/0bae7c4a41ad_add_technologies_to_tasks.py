"""add technologies to tasks

Revision ID: 0bae7c4a41ad
Revises: dfdbe7ec3b9b
Create Date: 2026-10-22 14:47:01.392843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bae7c4a41ad'
down_revision: Union[str, Sequence[str], None] = 'dfdbe7ec3b9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tarefa",
        sa.Column("technologies", sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tarefa", "technologies")
