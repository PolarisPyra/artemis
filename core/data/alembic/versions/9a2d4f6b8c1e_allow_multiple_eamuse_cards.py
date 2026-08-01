"""Allow multiple Konami cards per account."""

from alembic import op


revision = "9a2d4f6b8c1e"
down_revision = "8f1c3a7e5b2d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("eamuse_card_user_idx", "eamuse_card", ["user"])
    op.drop_constraint("eamuse_card_user_uk", "eamuse_card", type_="unique")


def downgrade():
    op.drop_index("eamuse_card_user_idx", table_name="eamuse_card")
    op.create_unique_constraint("eamuse_card_user_uk", "eamuse_card", ["user"])
