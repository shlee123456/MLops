"""add fewshot_messages table

Revision ID: c993e5b04484
Revises: c16ca4e3757a
Create Date: 2026-01-25 22:41:37.379296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c993e5b04484'
down_revision: Union[str, None] = 'c16ca4e3757a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('fewshot_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('llm_config_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['llm_config_id'], ['llm_configs.id'], name='fk_fewshot_messages_llm_config_id'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('fewshot_messages')
