"""Merge the shared, e-amusement, and legacy Konami migration heads."""

from typing import Sequence, Union


revision: str = "merge_artemis_heads"
down_revision: Union[str, Sequence[str], None] = (
    "263169f3a129",
    "696b0264ab74",
    "a8d1f6e2c4b7",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
