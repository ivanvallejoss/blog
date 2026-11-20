"""add content_toc to post

Revision ID: f2e2656089ac
Revises: 5dbb53bedbee
Create Date: 2026-07-30 15:43:13.597736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2e2656089ac'
down_revision: Union[str, Sequence[str], None] = '5dbb53bedbee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'posts',
        sa.Column(
            'content_toc',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('posts', 'content_toc')