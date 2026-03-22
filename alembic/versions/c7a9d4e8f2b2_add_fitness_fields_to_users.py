"""Add fitness_score and fitness_level to users

Revision ID: c7a9d4e8f2b2
Revises: b3d4f2b9c1a1
Create Date: 2026-02-27 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7a9d4e8f2b2"
down_revision: Union[str, Sequence[str], None] = "b3d4f2b9c1a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("fitness_score", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("fitness_level", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "fitness_level")
    op.drop_column("users", "fitness_score")
