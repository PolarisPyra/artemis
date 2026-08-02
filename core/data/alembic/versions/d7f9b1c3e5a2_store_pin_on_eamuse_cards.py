"""Store Konami PINs on cards and associate refids with cards."""

import sqlalchemy as sa
from alembic import op


revision = "d7f9b1c3e5a2"
down_revision = "c6e8a2d4f0b1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("eamuse_card", sa.Column("pin", sa.CHAR(length=4), nullable=True))
    op.add_column("refid", sa.Column("eamuse_card", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "refid_eamuse_card_fk",
        "refid",
        "eamuse_card",
        ["eamuse_card"],
        ["id"],
        ondelete="SET NULL",
        onupdate="CASCADE",
    )

    bind = op.get_bind()
    bind.execute(sa.text("""
        UPDATE eamuse_card ec
        INNER JOIN aime_user au ON au.id = ec.user
        SET ec.pin = au.pin
        WHERE au.pin IS NOT NULL
    """))
    bind.execute(sa.text("""
        UPDATE refid r
        INNER JOIN aime_card ac ON ac.user = r.user
        SET r.eamuse_card = ac.primary_eamuse_card
        WHERE r.eamuse_card IS NULL
          AND ac.primary_eamuse_card IS NOT NULL
    """))

    op.drop_column("aime_user", "pin")


def downgrade():
    op.add_column("aime_user", sa.Column("pin", sa.CHAR(length=4), nullable=True))
    bind = op.get_bind()
    bind.execute(sa.text("""
        UPDATE aime_user au
        INNER JOIN eamuse_card ec ON ec.user = au.id
        SET au.pin = ec.pin
        WHERE au.pin IS NULL
          AND ec.pin IS NOT NULL
    """))
    op.drop_constraint("refid_eamuse_card_fk", "refid", type_="foreignkey")
    op.drop_column("refid", "eamuse_card")
    op.drop_column("eamuse_card", "pin")
