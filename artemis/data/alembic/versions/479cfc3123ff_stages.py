"""stages

Revision ID: 479cfc3123ff
Revises: fe44e84cf890
Create Date: 2025-09-10 23:08:47.388290

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "479cfc3123ff"
down_revision = "fe44e84cf890"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cozynet_static_stages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("opt", mysql.BIGINT(), nullable=True),
        sa.Column("stageId", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("imagePath", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", "stageId", name="cozynet_static_stages_uk"),
        mysql_charset="utf8mb4",
    )
    op.create_foreign_key(
        None,
        "cozynet_static_stages",
        "chuni_static_opts",
        ["opt"],
        ["id"],
        onupdate="cascade",
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_table("cozynet_static_stages")
