"""add lang and excerpt to post

Revision ID: a7c41e9b2d05
Revises: f2e2656089ac
Create Date: 2026-11-20 10:00:00.000000

Un post tiene un solo idioma (`lang`, 'es' o 'en'); su traducción, si existe,
es otro post. Los posts existentes quedan en español por el server_default.
`excerpt` es la bajada escrita a mano (propiedad «Resumen» de Notion).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c41e9b2d05'
down_revision: Union[str, Sequence[str], None] = 'f2e2656089ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'posts',
        sa.Column('lang', sa.String(length=2), nullable=False, server_default=sa.text("'es'")),
    )
    op.create_check_constraint('ck_posts_lang', 'posts', "lang IN ('es', 'en')")
    op.create_index('ix_posts_lang', 'posts', ['lang'])
    op.add_column('posts', sa.Column('excerpt', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('posts', 'excerpt')
    op.drop_index('ix_posts_lang', table_name='posts')
    op.drop_constraint('ck_posts_lang', 'posts', type_='check')
    op.drop_column('posts', 'lang')
