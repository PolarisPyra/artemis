"""create Chunithm MATE item storage

Revision ID: 7f3c2a1e9b4d
Revises: 9e3b5c7d1f2a
"""

import sqlalchemy as sa
from alembic import op


revision = "7f3c2a1e9b4d"
down_revision = "9e3b5c7d1f2a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chuni_item_mate",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("mateId", sa.Integer(), nullable=True),
        sa.Column("playCount", sa.Integer(), nullable=True),
        sa.Column("enterGardenCount", sa.Integer(), nullable=True),
        sa.Column("friendshipLevel", sa.Integer(), nullable=True),
        sa.Column("totalFriendshipExp", sa.Integer(), nullable=True),
        sa.Column("totalUsePoint", sa.Integer(), nullable=True),
        sa.Column("isValid", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user"], ["aime_user.id"], ondelete="cascade", onupdate="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user", "version", "mateId", name="chuni_item_mate_uk"),
        mysql_charset="utf8mb4",
    )


def downgrade():
    op.drop_table("chuni_item_mate")
