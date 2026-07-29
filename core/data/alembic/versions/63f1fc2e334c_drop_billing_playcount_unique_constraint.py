"""drop billing playcount unique constraint

Revision ID: 63f1fc2e334c
Revises: 1b78db5898f4
Create Date: 2026-07-03 18:01:52.160242

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63f1fc2e334c'
down_revision = '1b78db5898f4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('machine', 'machine_billing_playcount', type_='unique')


def downgrade():
    op.create_unique_constraint('machine', 'machine_billing_playcount', ['machine'])
