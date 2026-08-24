"""Align Pop'n static music versions with the arcade release order."""

import sqlalchemy as sa
from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            """
            UPDATE popn_static_music
            SET version = -100 - version
            WHERE version BETWEEN 23 AND 29
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE old
            FROM popn_static_music old
            INNER JOIN popn_static_music keep
                ON keep.version IN (-128, -129)
                AND old.version IN (-128, -129)
                AND old.songId <=> keep.songId
                AND old.chartId <=> keep.chartId
                AND old.id > keep.id
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE popn_static_music
            SET version = CASE version
                WHEN -123 THEN 27
                WHEN -124 THEN 28
                WHEN -125 THEN 29
                WHEN -126 THEN 30
                WHEN -127 THEN 31
                WHEN -128 THEN 32
                WHEN -129 THEN 32
                ELSE version
            END
            WHERE version BETWEEN -129 AND -123
            """
        )
    )


def downgrade():
    op.execute(
        sa.text(
            """
            UPDATE popn_static_music
            SET version = CASE version
                WHEN 27 THEN 23
                WHEN 28 THEN 24
                WHEN 29 THEN 25
                WHEN 30 THEN 26
                WHEN 31 THEN 27
                WHEN 32 THEN 28
                ELSE version
            END
            WHERE version BETWEEN 27 AND 32
            """
        )
    )
