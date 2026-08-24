"""Move Pop'n High☆Cheers static data to version 29."""

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            "UPDATE popn_static_music SET version = 29 WHERE version = 28"
        )
    )


def downgrade():
    op.execute(
        sa.text(
            "UPDATE popn_static_music SET version = 28 WHERE version = 29"
        )
    )
