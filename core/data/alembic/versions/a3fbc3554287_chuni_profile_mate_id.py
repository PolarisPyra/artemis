"""chuni profile mate id

Revision ID: a3fbc3554287
Revises: 385398a9b353
Create Date: 2026-07-07 10:29:14.879514

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "a3fbc3554287"
down_revision = "385398a9b353"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("chuni_profile_data", sa.Column("mateId", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("chuni_profile_data", "mateId")
