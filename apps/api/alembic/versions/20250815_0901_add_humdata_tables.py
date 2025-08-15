"""add humdata tables

Revision ID: 20250815_0901
Revises: 20250815_0852
Create Date: 2025-08-15 09:01:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20250815_0901'
down_revision = '20250815_0852'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'crises',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('country', sa.String(length=200)),
        sa.Column('url', sa.Text()),
        sa.Column('published_at', sa.DateTime()),
        sa.Column('raw', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.UniqueConstraint('source_id', name='uq_crises_source_id')
    )
    op.create_index('ix_crises_source', 'crises', ['source'])

    op.create_table(
        'job_postings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('org', sa.String(length=255)),
        sa.Column('location', sa.String(length=255)),
        sa.Column('url', sa.Text()),
        sa.Column('published_at', sa.DateTime()),
        sa.Column('deadline', sa.DateTime()),
        sa.Column('raw', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.UniqueConstraint('source_id', name='uq_jobs_source_id')
    )
    op.create_index('ix_job_postings_source', 'job_postings', ['source'])

    op.create_table(
        'funding_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer()),
        sa.Column('country', sa.String(length=200)),
        sa.Column('cluster', sa.String(length=200)),
        sa.Column('donor', sa.String(length=255)),
        sa.Column('recipient', sa.String(length=255)),
        sa.Column('amount', sa.Float()),
        sa.Column('currency', sa.String(length=10)),
        sa.Column('raw', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('ix_funding_records_source', 'funding_records', ['source'])
    op.create_index('ix_funding_records_year', 'funding_records', ['year'])
    op.create_index('ix_funding_records_country', 'funding_records', ['country'])
    op.create_index('ix_funding_records_cluster', 'funding_records', ['cluster'])


def downgrade():
    op.drop_index('ix_funding_records_cluster', table_name='funding_records')
    op.drop_index('ix_funding_records_country', table_name='funding_records')
    op.drop_index('ix_funding_records_year', table_name='funding_records')
    op.drop_index('ix_funding_records_source', table_name='funding_records')
    op.drop_table('funding_records')

    op.drop_index('ix_job_postings_source', table_name='job_postings')
    op.drop_table('job_postings')

    op.drop_index('ix_crises_source', table_name='crises')
    op.drop_table('crises')
