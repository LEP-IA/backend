"""add complexity to tasks

Revision ID: 820d7c1eb3de
Revises: 0bae7c4a41ad
Create Date: 2026-10-22 15:05:55.094516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '820d7c1eb3de'
down_revision: Union[str, Sequence[str], None] = '0bae7c4a41ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tarefa", sa.Column("complexity", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tarefa", "complexity")
