"""Link Pop'n profiles to their ARTEMiS users."""

from alembic import op

import sqlalchemy as sa


revision = "9e3b5c7d1f2a"
down_revision = "8d2f4a6b9c1e"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "popn_profile_user_fk"


def _has_constraint() -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(
        foreign_key.get("name") == CONSTRAINT_NAME
        for foreign_key in inspector.get_foreign_keys("popn_profile")
    )


def upgrade():
    # The original profile migration builds its table from the current schema
    # object, so a fresh install may already contain this constraint. Existing
    # installs need it added here.
    if not _has_constraint():
        op.create_foreign_key(
            CONSTRAINT_NAME,
            "popn_profile",
            "aime_user",
            ["user"],
            ["id"],
            onupdate="cascade",
            ondelete="cascade",
        )


def downgrade():
    if _has_constraint():
        op.drop_constraint(CONSTRAINT_NAME, "popn_profile", type_="foreignkey")
