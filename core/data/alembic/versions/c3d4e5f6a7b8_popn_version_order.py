"""Align Pop'n static music versions with the arcade release order."""

import sqlalchemy as sa
from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            """
            UPDATE popn_static_music
            SET version = 32
            WHERE version = 29
            """
        )
    )


def downgrade():
    op.execute(
        sa.text(
            """
            UPDATE popn_static_music
            SET version = 29
            WHERE version = 32
            """
        )
    )
