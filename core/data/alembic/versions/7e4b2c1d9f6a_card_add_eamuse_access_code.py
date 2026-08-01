"""Add the account-bound Konami E004 card identifier."""

import sqlalchemy as sa
from alembic import op


revision = "7e4b2c1d9f6a"
down_revision = "merge_artemis_heads"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("aime_card")}
    if "eamuse_access_code" not in columns:
        op.add_column(
            "aime_card",
            sa.Column("eamuse_access_code", sa.String(length=16), nullable=True),
        )

    indexes = {
        index["name"]
        for index in inspector.get_indexes("aime_card")
        if index.get("unique")
    }
    if "aime_card_eamuse_access_code_uk" not in indexes:
        op.create_unique_constraint(
            "aime_card_eamuse_access_code_uk",
            "aime_card",
            ["eamuse_access_code"],
        )


def downgrade():
    op.drop_constraint(
        "aime_card_eamuse_access_code_uk", "aime_card", type_="unique"
    )
    op.drop_column("aime_card", "eamuse_access_code")
