"""add explicit PCBID to machines

Revision ID: 0d4d7f6c2a91
Revises: merge_artemis_heads
"""

from alembic import op
import sqlalchemy as sa


revision = "0d4d7f6c2a91"
down_revision = "merge_artemis_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("machine", sa.Column("pcbid", sa.CHAR(length=20), nullable=True))
    op.execute(
        "UPDATE machine SET pcbid = CONCAT('0120', serial) "
        "WHERE pcbid IS NULL AND serial REGEXP '^[0-9A-Fa-f]{16}$'"
    )
    op.create_index("machine_pcbid_ix", "machine", ["pcbid"], unique=True)


def downgrade() -> None:
    op.drop_index("machine_pcbid_ix", table_name="machine")
    op.drop_column("machine", "pcbid")
