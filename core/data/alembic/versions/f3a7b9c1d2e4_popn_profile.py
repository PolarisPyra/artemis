"""Create the standalone Pop'n profile table."""

from alembic import op

from titles.popn.schema.profile import profile


revision = "f3a7b9c1d2e4"
down_revision = "merge_artemis_heads"
branch_labels = None
depends_on = None


def upgrade():
    profile.create(bind=op.get_bind(), checkfirst=True)


def downgrade():
    profile.drop(bind=op.get_bind(), checkfirst=True)
