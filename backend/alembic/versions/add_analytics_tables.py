"""Add analytics and metrics tables

Revision ID: analytics_001
Revises: tool_execution_001
Create Date: 2025-08-22 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'analytics_001'
down_revision = 'tool_execution_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create metrics_aggregates table
    op.create_table(
        'metrics_aggregates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('metric_date', sa.DateTime(), nullable=False),
        sa.Column('total_calls', sa.Integer(), nullable=True, default=0),
        sa.Column('successful_calls', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_calls', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_response_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('min_response_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('max_response_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('p95_response_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('timeout_errors', sa.Integer(), nullable=True, default=0),
        sa.Column('auth_errors', sa.Integer(), nullable=True, default=0),
        sa.Column('rate_limit_errors', sa.Integer(), nullable=True, default=0),
        sa.Column('connectivity_errors', sa.Integer(), nullable=True, default=0),
        sa.Column('other_errors', sa.Integer(), nullable=True, default=0),
        sa.Column('tool_usage', sa.JSON(), nullable=True, default={}),
        sa.Column('estimated_cost', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('integration_id', 'metric_type', 'metric_date', name='uk_metrics_aggregate_unique')
    )
    
    # Create indexes for metrics_aggregates
    op.create_index('idx_metrics_aggregate_integration_type_date', 'metrics_aggregates', ['integration_id', 'metric_type', 'metric_date'])
    op.create_index('idx_metrics_aggregate_date_type', 'metrics_aggregates', ['metric_date', 'metric_type'])
    op.create_index(op.f('ix_metrics_aggregates_integration_id'), 'metrics_aggregates', ['integration_id'])
    op.create_index(op.f('ix_metrics_aggregates_metric_type'), 'metrics_aggregates', ['metric_type'])
    op.create_index(op.f('ix_metrics_aggregates_metric_date'), 'metrics_aggregates', ['metric_date'])
    
    # Create integration_health_snapshots table
    op.create_table(
        'integration_health_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=True, default=0.0),
        sa.Column('uptime_percentage', sa.Float(), nullable=True, default=0.0),
        sa.Column('error_count_24h', sa.Integer(), nullable=True, default=0),
        sa.Column('connectivity_check', sa.String(20), nullable=True, default='unknown'),
        sa.Column('auth_check', sa.String(20), nullable=True, default='unknown'),
        sa.Column('rate_limit_check', sa.String(20), nullable=True, default='unknown'),
        sa.Column('health_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('metadata', sa.JSON(), nullable=True, default={}),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for integration_health_snapshots
    op.create_index('idx_health_snapshot_integration_time', 'integration_health_snapshots', ['integration_id', 'snapshot_time'])
    op.create_index('idx_health_snapshot_time', 'integration_health_snapshots', ['snapshot_time'])
    op.create_index('idx_health_snapshot_status', 'integration_health_snapshots', ['status', 'snapshot_time'])
    op.create_index(op.f('ix_integration_health_snapshots_integration_id'), 'integration_health_snapshots', ['integration_id'])
    
    # Create cost_tracking table
    op.create_table(
        'cost_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('billing_period', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_api_calls', sa.Integer(), nullable=True, default=0),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=True, default=0.0),
        sa.Column('cost_per_call', sa.Float(), nullable=True, default=0.0),
        sa.Column('usage_by_tool', sa.JSON(), nullable=True, default={}),
        sa.Column('usage_by_day', sa.JSON(), nullable=True, default={}),
        sa.Column('cost_model', sa.String(50), nullable=True, default='estimated'),
        sa.Column('currency', sa.String(3), nullable=True, default='USD'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('integration_id', 'billing_period', 'period_start', name='uk_cost_tracking_unique')
    )
    
    # Create indexes for cost_tracking
    op.create_index('idx_cost_tracking_user_period', 'cost_tracking', ['user_id', 'period_start'])
    op.create_index('idx_cost_tracking_integration_period', 'cost_tracking', ['integration_id', 'period_start'])
    op.create_index(op.f('ix_cost_tracking_integration_id'), 'cost_tracking', ['integration_id'])
    op.create_index(op.f('ix_cost_tracking_user_id'), 'cost_tracking', ['user_id'])
    op.create_index(op.f('ix_cost_tracking_billing_period'), 'cost_tracking', ['billing_period'])


def downgrade():
    # Drop cost_tracking table and indexes
    op.drop_index(op.f('ix_cost_tracking_billing_period'), table_name='cost_tracking')
    op.drop_index(op.f('ix_cost_tracking_user_id'), table_name='cost_tracking')
    op.drop_index(op.f('ix_cost_tracking_integration_id'), table_name='cost_tracking')
    op.drop_index('idx_cost_tracking_integration_period', table_name='cost_tracking')
    op.drop_index('idx_cost_tracking_user_period', table_name='cost_tracking')
    op.drop_table('cost_tracking')
    
    # Drop integration_health_snapshots table and indexes
    op.drop_index(op.f('ix_integration_health_snapshots_integration_id'), table_name='integration_health_snapshots')
    op.drop_index('idx_health_snapshot_status', table_name='integration_health_snapshots')
    op.drop_index('idx_health_snapshot_time', table_name='integration_health_snapshots')
    op.drop_index('idx_health_snapshot_integration_time', table_name='integration_health_snapshots')
    op.drop_table('integration_health_snapshots')
    
    # Drop metrics_aggregates table and indexes
    op.drop_index(op.f('ix_metrics_aggregates_metric_date'), table_name='metrics_aggregates')
    op.drop_index(op.f('ix_metrics_aggregates_metric_type'), table_name='metrics_aggregates')
    op.drop_index(op.f('ix_metrics_aggregates_integration_id'), table_name='metrics_aggregates')
    op.drop_index('idx_metrics_aggregate_date_type', table_name='metrics_aggregates')
    op.drop_index('idx_metrics_aggregate_integration_type_date', table_name='metrics_aggregates')
    op.drop_table('metrics_aggregates')