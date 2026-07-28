"""chunithm verse pt.2

Revision ID: 6140c87aa666
Revises: 333b18ea651e
Create Date: 2024-12-16 09:39:56.443840

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6140c87aa666"
down_revision = "333b18ea651e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chuni_score_playlog",
        sa.Column(
            "monthPoint", sa.Integer(), nullable=True, server_default=sa.text("NULL")
        ),
    )
    op.add_column(
        "chuni_score_playlog",
        sa.Column(
            "eventPoint", sa.Integer(), nullable=True, server_default=sa.text("NULL")
        ),
    )


def downgrade():
    op.drop_column("chuni_score_playlog", "eventPoint")
    op.drop_column("chuni_score_playlog", "monthPoint")
