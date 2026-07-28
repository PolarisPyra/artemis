"""Reserve the historical Konami document revision.

Konami documents are now created in the separate ``konami`` database by
Artemis' database bootstrap. This revision remains in the main migration
chain only so existing databases can advance without creating a Konami table
inside the Artemis database.

Revision ID: a8d1f6e2c4b7
Revises: a3fbc3554287
"""

revision = "a8d1f6e2c4b7"
down_revision = "a3fbc3554287"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
