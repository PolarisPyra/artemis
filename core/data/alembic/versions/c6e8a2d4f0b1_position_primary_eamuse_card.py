"""Place the primary Konami card reference beside access_code."""

import sqlalchemy as sa
from alembic import op


revision = "c6e8a2d4f0b1"
down_revision = "b5d7f9a1c3e6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            "ALTER TABLE aime_card MODIFY COLUMN primary_eamuse_card "
            "INT NULL AFTER access_code"
        )
    )


def downgrade():
    op.execute(
        sa.text(
            "ALTER TABLE aime_card MODIFY COLUMN primary_eamuse_card "
            "INT NULL AFTER memo"
        )
    )
