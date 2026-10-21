"""add professional and board member profiles

Revision ID: dfdbe7ec3b9b
Revises: a6a91b755ce7
Create Date: 2026-10-21 17:39:47.691486

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "dfdbe7ec3b9b"
down_revision: Union[str, Sequence[str], None] = "a6a91b755ce7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Perfil profissional geral do usuário
    op.create_table(
        "perfil_profissional",
        sa.Column("usuario_email", sa.String(), nullable=False),
        sa.Column("area", sa.String(), nullable=True),
        sa.Column("profession", sa.String(), nullable=True),
        sa.Column("specialization", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("seniority", sa.String(), nullable=True),
        sa.Column("experience_time", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_email"],
            ["usuario.email"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("usuario_email"),
    )

    # Perfil do usuário dentro do Board
    op.add_column(
        "board_membro",
        sa.Column("project_role", sa.String(), nullable=True),
    )

    op.add_column(
        "board_membro",
        sa.Column("participation_type", sa.String(), nullable=True),
    )

    op.add_column(
        "board_membro",
        sa.Column("weekly_hours", sa.Integer(), nullable=True),
    )

    # Garante apenas um registro do usuário por Board
    op.create_unique_constraint(
        "uq_board_membro",
        "board_membro",
        ["board_id", "usuario_email"],
    )

    # Garante intervalo válido de horas semanais
    op.create_check_constraint(
        "ck_board_membro_weekly_hours",
        "board_membro",
        "weekly_hours IS NULL OR " "(weekly_hours >= 0 AND weekly_hours <= 168)",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_board_membro_weekly_hours",
        "board_membro",
        type_="check",
    )

    op.drop_constraint(
        "uq_board_membro",
        "board_membro",
        type_="unique",
    )

    op.drop_column("board_membro", "weekly_hours")
    op.drop_column("board_membro", "participation_type")
    op.drop_column("board_membro", "project_role")

    op.drop_table("perfil_profissional")
