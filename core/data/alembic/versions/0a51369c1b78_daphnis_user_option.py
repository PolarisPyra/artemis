"""daphnis_user_option

Revision ID: 0a51369c1b78
Revises: e8db52e6b7fa
Create Date: 2024-12-20 10:35:03.852023

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0a51369c1b78"
down_revision = "e8db52e6b7fa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daphnis_user_option",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["user"], ["aime_user.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
    )


def downgrade():
    op.drop_table("daphnis_user_option")
