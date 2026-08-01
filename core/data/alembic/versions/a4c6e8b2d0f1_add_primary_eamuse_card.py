"""Add an optional primary Konami card to each account."""

import sqlalchemy as sa
from alembic import op


revision = "a4c6e8b2d0f1"
down_revision = "9a2d4f6b8c1e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "aime_user",
        sa.Column("primary_eamuse_card", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "aime_user_primary_eamuse_card_fk",
        "aime_user",
        "eamuse_card",
        ["primary_eamuse_card"],
        ["id"],
        ondelete="SET NULL",
        onupdate="CASCADE",
    )


def downgrade():
    op.drop_constraint("aime_user_primary_eamuse_card_fk", "aime_user", type_="foreignkey")
    op.drop_column("aime_user", "primary_eamuse_card")
