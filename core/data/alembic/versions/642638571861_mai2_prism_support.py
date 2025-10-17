"""mai2 prism support

Revision ID: 642638571861
Revises: 6c6e2e43254d
Create Date: 2025-10-17 04:47:57.005390

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "642638571861"
down_revision = "6c6e2e43254d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mai2_score_kaleidxscope",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user", sa.Integer(), nullable=False),
        sa.Column("gateId", sa.Integer(), nullable=True),
        sa.Column("isGateFound", sa.Boolean(), nullable=True),
        sa.Column("isKeyFound", sa.Boolean(), nullable=True),
        sa.Column("isClear", sa.Boolean(), nullable=True),
        sa.Column("totalRestLife", sa.Integer(), nullable=True),
        sa.Column("totalAchievement", sa.Integer(), nullable=True),
        sa.Column("totalDeluxscore", sa.Integer(), nullable=True),
        sa.Column("bestAchievement", sa.Integer(), nullable=True),
        sa.Column("bestDeluxscore", sa.Integer(), nullable=True),
        sa.Column("bestAchievementDate", sa.String(length=25), nullable=True),
        sa.Column("bestDeluxscoreDate", sa.String(length=25), nullable=True),
        sa.Column("playCount", sa.Integer(), nullable=True),
        sa.Column("clearDate", sa.String(length=25), nullable=True),
        sa.Column("lastPlayDate", sa.String(length=25), nullable=True),
        sa.Column("isInfoWatched", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user"], ["aime_user.id"], onupdate="cascade", ondelete="cascade"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user", "gateId", name="mai2_score_best_uk"),
        mysql_charset="utf8mb4",
    )
    op.add_column(
        "mai2_playlog",
        sa.Column(
            "extBool2", sa.Boolean(), nullable=True, server_default=sa.text("NULL")
        ),
    )
    op.add_column(
        "mai2_playlog",
        sa.Column(
            "extBool3", sa.Boolean(), nullable=True, server_default=sa.text("NULL")
        ),
    )


def downgrade():
    op.drop_column("mai2_playlog", "extBool3")
    op.drop_column("mai2_playlog", "extBool2")
    op.drop_table("mai2_score_kaleidxscope")
