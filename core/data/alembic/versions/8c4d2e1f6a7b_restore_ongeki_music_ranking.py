"""restore Ongeki static music rankings

Revision ID: 8c4d2e1f6a7b
Revises: 7f3c2a1e9b4d
"""

import sqlalchemy as sa
from alembic import op


revision = "8c4d2e1f6a7b"
down_revision = "7f3c2a1e9b4d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ongeki_static_music_ranking_list",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("musicId", sa.Integer(), nullable=False),
        sa.Column("point", sa.Integer(), nullable=False),
        sa.Column("userName", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", "musicId", name="ongeki_static_music_ranking_uk"),
        mysql_charset="utf8mb4",
    )


def downgrade():
    op.drop_table("ongeki_static_music_ranking_list")
