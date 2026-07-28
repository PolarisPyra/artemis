"""chunithm x-verse

Revision ID: fe44e84cf890
Revises: a3c977d84090
Create Date: 2025-07-30 11:23:52.779089

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fe44e84cf890"
down_revision = "a3c977d84090"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chuni_profile_linked_verse",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user", sa.Integer(), nullable=False),
        sa.Column("linkedVerseId", sa.Integer(), nullable=False),
        sa.Column("progress", sa.String(length=255), nullable=True),
        sa.Column("statusOpen", sa.Integer(), nullable=True),
        sa.Column("statusUnlock", sa.Integer(), nullable=True),
        sa.Column("isFirstClear", sa.Integer(), nullable=True),
        sa.Column("numClear", sa.Integer(), nullable=True),
        sa.Column("clearCourseId", sa.Integer(), nullable=True),
        sa.Column("clearCourseLevel", sa.Integer(), nullable=True),
        sa.Column("clearScore", sa.Integer(), nullable=True),
        sa.Column("clearDate", sa.String(length=25), nullable=True),
        sa.Column("clearUserId1", sa.Integer(), nullable=True),
        sa.Column("clearUserId2", sa.Integer(), nullable=True),
        sa.Column("clearUserId3", sa.Integer(), nullable=True),
        sa.Column("clearUserName1", sa.String(length=20), nullable=True),
        sa.Column("clearUserName2", sa.String(length=20), nullable=True),
        sa.Column("clearUserName3", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(
            ["user"], ["aime_user.id"], onupdate="cascade", ondelete="cascade"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user", "linkedVerseId", name="chuni_profile_linked_verse_uk"
        ),
        mysql_charset="utf8mb4",
    )
    op.add_column(
        "chuni_profile_data",
        sa.Column(
            "stageId", sa.Integer(), server_default=sa.text("-1"), nullable=False
        ),
    )


def downgrade():
    op.drop_column("chuni_profile_data", "stageId")
    op.drop_table("chuni_profile_linked_verse")
