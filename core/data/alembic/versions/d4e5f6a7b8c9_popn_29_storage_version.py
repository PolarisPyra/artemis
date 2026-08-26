"""Store Pop'n High☆Cheers data and REFIDs as version 29."""

import sqlalchemy as sa
from alembic import op


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            "UPDATE popn_static_music SET version = 29 WHERE version = 32"
        )
    )
    op.execute(
        sa.text(
            "UPDATE refid SET version = 29 WHERE game = 'M39' AND version = 32"
        )
    )


def downgrade():
    op.execute(
        sa.text(
            "UPDATE popn_static_music SET version = 32 WHERE version = 29"
        )
    )
    op.execute(
        sa.text(
            "UPDATE refid SET version = 32 WHERE game = 'M39' AND version = 29"
        )
    )
