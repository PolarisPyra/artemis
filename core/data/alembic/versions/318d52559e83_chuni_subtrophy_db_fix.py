"""chuni_subtrophy_db_fix

Revision ID: 318d52559e83
Revises: 8b57e9646449
Create Date: 2026-01-08 19:13:29.803912

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '318d52559e83'
down_revision = '8b57e9646449'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('chuni_profile_data', 'trophyIdSub1', existing_type=mysql.INTEGER(), server_default='-1')
    op.alter_column('chuni_profile_data', 'trophyIdSub2', existing_type=mysql.INTEGER(), server_default='-1')

    # fix any current profiles where the bad defaults were used
    op.execute("UPDATE chuni_profile_data SET trophyIdSub1=-1 WHERE trophyIdSub1 IS NULL")
    op.execute("UPDATE chuni_profile_data SET trophyIdSub2=-1 WHERE trophyIdSub2 IS NULL")


def downgrade():
    # dont bother "unfixing" the table
    pass
