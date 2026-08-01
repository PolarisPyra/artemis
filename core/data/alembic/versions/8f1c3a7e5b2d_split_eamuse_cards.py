"""Move Konami cards out of aime_card into eamuse_card."""

import sqlalchemy as sa
from alembic import op


revision = "8f1c3a7e5b2d"
down_revision = "7e4b2c1d9f6a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "eamuse_card",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user", sa.Integer(), nullable=False),
        sa.Column("access_code", sa.String(length=16), nullable=False),
        sa.Column("idm", sa.String(length=16), nullable=True),
        sa.Column("created_date", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_login_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("is_locked", sa.Boolean(), server_default="0"),
        sa.Column("is_banned", sa.Boolean(), server_default="0"),
        sa.Column("memo", sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(["user"], ["aime_user.id"], ondelete="cascade", onupdate="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("access_code", name="eamuse_card_access_code_uk"),
        sa.UniqueConstraint("idm", name="eamuse_card_idm_uk"),
        sa.UniqueConstraint("user", name="eamuse_card_user_uk"),
        mysql_charset="utf8mb4",
    )

    bind = op.get_bind()
    bind.execute(sa.text("""
        INSERT INTO eamuse_card
            (user, access_code, idm, created_date, last_login_date, is_locked, is_banned, memo)
        SELECT source.user,
               source.eamuse_access_code,
               CASE WHEN source.idm = source.eamuse_access_code THEN NULL ELSE source.idm END,
               source.created_date,
               source.last_login_date,
               source.is_locked,
               source.is_banned,
               source.memo
        FROM aime_card source
        INNER JOIN (
            SELECT user, MIN(id) AS id
            FROM aime_card
            WHERE eamuse_access_code IS NOT NULL
            GROUP BY user
        ) selected ON selected.id = source.id
    """))

    bind.execute(sa.text("""
        UPDATE aime_card
        SET idm = NULL
        WHERE eamuse_access_code IS NOT NULL
          AND idm = eamuse_access_code
          AND access_code IS NOT NULL
    """))
    bind.execute(sa.text("""
        DELETE FROM aime_card
        WHERE access_code IS NULL
          AND eamuse_access_code IS NOT NULL
    """))

    op.drop_constraint("aime_card_eamuse_access_code_uk", "aime_card", type_="unique")
    op.drop_column("aime_card", "eamuse_access_code")


def downgrade():
    op.add_column(
        "aime_card",
        sa.Column("eamuse_access_code", sa.String(length=16), nullable=True),
    )
    op.create_unique_constraint(
        "aime_card_eamuse_access_code_uk", "aime_card", ["eamuse_access_code"]
    )
    op.execute(sa.text("""
        UPDATE aime_card ac
        INNER JOIN eamuse_card ec ON ec.user = ac.user
        SET ac.eamuse_access_code = ec.access_code
        WHERE ac.access_code IS NOT NULL
    """))
    op.drop_table("eamuse_card")
