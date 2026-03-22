"""Add medical_conditions to users

Revision ID: b3d4f2b9c1a1
Revises: aa6859de720b
Create Date: 2026-02-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3d4f2b9c1a1"
down_revision: Union[str, Sequence[str], None] = "aa6859de720b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "medical_conditions",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.alter_column("users", "medical_conditions", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "medical_conditions")
