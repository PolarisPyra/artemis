"""Index the Pop'n playlog fields used for popularity responses."""

from alembic import op

revision = "e6f7a8b9c0d1"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_popn_playlog_music_num", "popn_playlog", ["music_num"]
    )
    op.create_index(
        "ix_popn_playlog_chara_num", "popn_playlog", ["chara_num"]
    )


def downgrade() -> None:
    op.drop_index("ix_popn_playlog_chara_num", table_name="popn_playlog")
    op.drop_index("ix_popn_playlog_music_num", table_name="popn_playlog")
