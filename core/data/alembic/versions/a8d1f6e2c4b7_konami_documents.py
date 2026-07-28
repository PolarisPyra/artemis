"""add native Konami document storage

Revision ID: a8d1f6e2c4b7
Revises: a3fbc3554287
"""

from alembic import op
import sqlalchemy as sa


revision = "a8d1f6e2c4b7"
down_revision = "a3fbc3554287"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "konami_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("refid", sa.String(length=32), nullable=False),
        sa.Column("game_code", sa.String(length=8), nullable=False),
        sa.Column("collection", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "refid", "game_code", "collection", "version", name="konami_document_uk"
        ),
        mysql_charset="utf8mb4",
    )


def downgrade():
    op.drop_table("konami_document")
