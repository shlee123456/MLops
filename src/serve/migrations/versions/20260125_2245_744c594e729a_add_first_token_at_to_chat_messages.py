"""add first_token_at to chat_messages

Revision ID: 744c594e729a
Revises: c993e5b04484
Create Date: 2026-01-25 22:45:54.589074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '744c594e729a'
down_revision: Union[str, None] = 'c993e5b04484'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('first_token_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_messages', 'first_token_at')
