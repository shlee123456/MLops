"""add user_id fk to conversations

Revision ID: c16ca4e3757a
Revises: c61a688f053c
Create Date: 2026-01-25 22:39:26.601494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c16ca4e3757a'
down_revision: Union[str, None] = 'c61a688f053c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite batch mode for FK constraint support
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_conversations_user_id', 'users', ['user_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_conversations_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
