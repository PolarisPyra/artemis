"""create Pop'n static music storage

Revision ID: 9d5e3f2a1b7c
Revises: 8c4d2e1f6a7b
"""

import sqlalchemy as sa
from alembic import op


revision = "9d5e3f2a1b7c"
down_revision = "8c4d2e1f6a7b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "popn_static_music",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("songId", sa.Integer(), nullable=True),
        sa.Column("chartId", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("artist", sa.String(length=255), nullable=True),
        sa.Column("genre", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", "songId", "chartId", name="popn_static_music_uk"),
        mysql_charset="utf8mb4",
    )


def downgrade():
    op.drop_table("popn_static_music")
