"""Adiciona colunas personalizadas aos boards"""

from alembic import op
import sqlalchemy as sa

# identificação da migração
revision = "f12a6c9b4d01"
down_revision = "c8f3d1a6e902"
branch_labels = None
depends_on = None


def upgrade():
    # cria tabela de colunas
    op.create_table(
        "board_column",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("board_id", sa.Integer(), nullable=False),
        sa.Column("status_key", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("posicao", sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint("id"),

        sa.ForeignKeyConstraint(
            ["board_id"],
            ["board.id_board"],
            ondelete="CASCADE",
        ),

        sa.UniqueConstraint(
            "board_id",
            "status_key",
            name="uq_board_column_status_key",
        ),
    )

    op.create_index(
        "ix_board_column_id",
        "board_column",
        ["id"],
    )

    # crias colunas padroes nos quadros existentes 
    op.execute("""
        INSERT INTO board_column
            (board_id, status_key, nome, posicao)
        SELECT
            b.id_board,
            c.status_key,
            c.nome,
            c.posicao
        FROM board b
        CROSS JOIN (
            VALUES
                ('BACKLOG', 'Backlog', 0),
                ('DOING', 'Em Andamento', 1),
                ('DONE', 'Concluído', 2)
        ) AS c(status_key, nome, posicao)
    """)

    # recupera colunas personalizadas que já possuem tarefas
    op.execute("""
        INSERT INTO board_column
            (board_id, status_key, nome, posicao)
        SELECT
            id_board,
            status,
            status,
            ROW_NUMBER() OVER (
                PARTITION BY id_board ORDER BY status
            ) + 2
        FROM (
            SELECT DISTINCT id_board, status
            FROM tarefa
            WHERE status NOT IN ('BACKLOG', 'DOING', 'DONE')
              AND TRIM(status) <> ''
        ) AS custom_columns
    """)


def downgrade():
    # remove a tabela caso a migraçao seja revertida
    op.drop_index(
        "ix_board_column_id",
        table_name="board_column",
    )

    op.drop_table("board_column")