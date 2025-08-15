"""
add users table and oauth_tokens.user_id

Revision ID: 20250815_0852
Revises: 
Create Date: 2025-08-15 08:52:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250815_0852'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    # Add user_id to oauth_tokens if not exists
    with op.batch_alter_table('oauth_tokens') as batch_op:
        batch_op.add_column(sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_oauth_tokens_user_id_users', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('oauth_tokens') as batch_op:
        try:
            batch_op.drop_constraint('fk_oauth_tokens_user_id_users', type_='foreignkey')
        except Exception:
            pass
        try:
            batch_op.drop_column('user_id')
        except Exception:
            pass
    op.drop_table('users')
