"""Move the primary Konami card reference onto aime_card."""

import sqlalchemy as sa
from alembic import op


revision = "b5d7f9a1c3e6"
down_revision = "a4c6e8b2d0f1"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("aime_user_primary_eamuse_card_fk", "aime_user", type_="foreignkey")
    op.drop_column("aime_user", "primary_eamuse_card")
    op.add_column(
        "aime_card",
        sa.Column("primary_eamuse_card", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "aime_card_primary_eamuse_card_fk",
        "aime_card",
        "eamuse_card",
        ["primary_eamuse_card"],
        ["id"],
        ondelete="SET NULL",
        onupdate="CASCADE",
    )


def downgrade():
    op.drop_constraint("aime_card_primary_eamuse_card_fk", "aime_card", type_="foreignkey")
    op.drop_column("aime_card", "primary_eamuse_card")
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
