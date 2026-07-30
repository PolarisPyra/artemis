"""Store Pop'n play results in a relational playlog table."""

from alembic import op

import sqlalchemy as sa


revision = "8d2f4a6b9c1e"
down_revision = "7c9f1b2e4d6a"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("popn_profile", "scores")
    op.create_table(
        "popn_playlog",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ref_id", sa.String(length=32), nullable=True),
        sa.Column("data_id", sa.String(length=32), nullable=True),
        sa.Column("name", sa.String(length=32), nullable=True),
        sa.Column("chara_num", sa.Integer(), nullable=True),
        sa.Column("mode", sa.Integer(), nullable=True),
        sa.Column("play_id", sa.Integer(), nullable=True),
        sa.Column("stage", sa.Integer(), nullable=True),
        sa.Column("music_num", sa.Integer(), nullable=True),
        sa.Column("sheet_num", sa.Integer(), nullable=True),
        sa.Column("clear_type", sa.Integer(), nullable=True),
        sa.Column("clear_rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("cool", sa.Integer(), nullable=True),
        sa.Column("great", sa.Integer(), nullable=True),
        sa.Column("good", sa.Integer(), nullable=True),
        sa.Column("bad", sa.Integer(), nullable=True),
        sa.Column("combo", sa.Integer(), nullable=True),
        sa.Column("highlight", sa.Integer(), nullable=True),
        sa.Column("gauge", sa.Integer(), nullable=True),
        sa.Column("gauge_type", sa.Integer(), nullable=True),
        sa.Column("is_netvs", sa.Integer(), nullable=True),
        sa.Column("is_win", sa.Integer(), nullable=True),
        sa.Column("is_image_store", sa.Boolean(), nullable=True),
        sa.Column("is_option_save", sa.Boolean(), nullable=True),
        sa.Column("hispeed", sa.Integer(), nullable=True),
        sa.Column("popkun", sa.Integer(), nullable=True),
        sa.Column("hidden", sa.Boolean(), nullable=True),
        sa.Column("hidden_rate", sa.Integer(), nullable=True),
        sa.Column("sudden", sa.Boolean(), nullable=True),
        sa.Column("sudden_rate", sa.Integer(), nullable=True),
        sa.Column("randmir", sa.Integer(), nullable=True),
        sa.Column("ojama_0", sa.Integer(), nullable=True),
        sa.Column("ojama_1", sa.Integer(), nullable=True),
        sa.Column("forever_0", sa.Boolean(), nullable=True),
        sa.Column("forever_1", sa.Boolean(), nullable=True),
        sa.Column("full_setting", sa.Boolean(), nullable=True),
        sa.Column("guide_se", sa.Integer(), nullable=True),
        sa.Column("guide_se_vol", sa.Integer(), nullable=True),
        sa.Column("lift", sa.Boolean(), nullable=True),
        sa.Column("lift_rate", sa.Integer(), nullable=True),
        sa.Column("judge_ad", sa.Integer(), nullable=True),
        sa.Column("roof", sa.Integer(), nullable=True),
        sa.Column("long_pop", sa.Integer(), nullable=True),
        sa.Column("judge", sa.Integer(), nullable=True),
        sa.Column("slow", sa.Integer(), nullable=True),
        sa.Column("fast", sa.Integer(), nullable=True),
        sa.Column("ex_gauge_lv", sa.Integer(), nullable=True),
        sa.Column("is_super_extra", sa.Integer(), nullable=True),
        sa.Column("netvs_ojama_type", sa.Integer(), nullable=True),
        sa.Column("netvs_type", sa.Integer(), nullable=True),
        sa.Column("netvs_rank", sa.Integer(), nullable=True),
        sa.Column("netvs_ojama_0", sa.Integer(), nullable=True),
        sa.Column("netvs_ojama_1", sa.Integer(), nullable=True),
        sa.Column("netvs_ojama_2", sa.Integer(), nullable=True),
        sa.Column("play_date", sa.BigInteger(), nullable=True),
        sa.Column("select_total_time", sa.Integer(), nullable=True),
        sa.Column("select_used_time", sa.Integer(), nullable=True),
        sa.Column("select_remain_time", sa.Integer(), nullable=True),
        sa.Column("category", sa.Integer(), nullable=True),
        sa.Column("sub_category", sa.Integer(), nullable=True),
        sa.Column("matching", sa.Integer(), nullable=True),
        sa.Column("ojama_vs", sa.Integer(), nullable=True),
        sa.Column("playdate", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["aime_user.id"], onupdate="cascade", ondelete="cascade"
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
    )


def downgrade():
    op.drop_table("popn_playlog")
    op.add_column("popn_profile", sa.Column("scores", sa.JSON(), nullable=True))
