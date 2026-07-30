"""Store the Hi~Cheers account, customization, and score state."""

from alembic import op

import sqlalchemy as sa


revision = "7c9f1b2e4d6a"
down_revision = "f3a7b9c1d2e4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("popn_profile", sa.Column("popn_class", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("popn_profile", sa.Column("option_tuto", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("popn_profile", sa.Column("sc_news_no", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("popn_profile", sa.Column("read_policy", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("popn_profile", sa.Column("language", sa.Integer(), nullable=False, server_default="0"))
    # JSON defaults are not supported consistently across the MySQL versions
    # supported by ARTEMiS. Existing rows are handled as empty state by the
    # Hi~Cheers reader, while newly-created profiles receive concrete values.
    op.add_column("popn_profile", sa.Column("customize", sa.JSON(), nullable=True))
    op.add_column("popn_profile", sa.Column("scores", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("popn_profile", "scores")
    op.drop_column("popn_profile", "customize")
    op.drop_column("popn_profile", "language")
    op.drop_column("popn_profile", "read_policy")
    op.drop_column("popn_profile", "sc_news_no")
    op.drop_column("popn_profile", "option_tuto")
    op.drop_column("popn_profile", "popn_class")
