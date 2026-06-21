"""split content into markdown and html

Revision ID: 27e5d28d1d3b
Revises: 776d692bc3cb
Create Date: 2026-06-19 08:46:19.018813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27e5d28d1d3b'
down_revision: Union[str, Sequence[str], None] = '776d692bc3cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        table_name="posts",
        column_name="content",
        new_column_name="content_markdown",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.add_column(
        "posts",
        sa.Column("content_html", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("posts", "content_html")

    op.alter_column(
        table_name="posts",
        column_name="content_markdown",
        new_column_name="content",
        existing_type=sa.Text(),
        nullable=False
    )
