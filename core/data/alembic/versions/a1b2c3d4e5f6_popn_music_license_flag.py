"""Store the MDB-derived Pop'n license flag."""

import sqlalchemy as sa
from alembic import op


revision = "a1b2c3d4e5f6"
down_revision = "d7f9b1c3e5a2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "popn_static_music",
        sa.Column("isLicense", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("popn_static_music", "isLicense")
