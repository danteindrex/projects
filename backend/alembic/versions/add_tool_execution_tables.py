"""Add tool execution tracking tables

Revision ID: tool_execution_001
Revises: add_oauth_support
Create Date: 2025-08-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'tool_execution_001'
down_revision = 'add_oauth_support'
branch_labels = None
depends_on = None


def upgrade():
    # Create tool_executions table
    op.create_table(
        'tool_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True, default={}),
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('result_data', sa.JSON(), nullable=True, default={}),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for tool_executions
    op.create_index('idx_tool_execution_session', 'tool_executions', ['session_id', 'started_at'])
    op.create_index('idx_tool_execution_user_time', 'tool_executions', ['user_id', 'started_at'])
    op.create_index('idx_tool_execution_integration_time', 'tool_executions', ['integration_id', 'started_at'])
    op.create_index('idx_tool_execution_tool_time', 'tool_executions', ['tool_name', 'started_at'])
    op.create_index(op.f('ix_tool_executions_tool_name'), 'tool_executions', ['tool_name'])
    op.create_index(op.f('ix_tool_executions_integration_id'), 'tool_executions', ['integration_id'])
    op.create_index(op.f('ix_tool_executions_session_id'), 'tool_executions', ['session_id'])
    op.create_index(op.f('ix_tool_executions_user_id'), 'tool_executions', ['user_id'])
    
    # Create tool_execution_events table
    op.create_table(
        'tool_execution_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True, default={}),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['tool_executions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for tool_execution_events
    op.create_index(op.f('ix_tool_execution_events_execution_id'), 'tool_execution_events', ['execution_id'])
    
    # Create streaming_events table
    op.create_table(
        'streaming_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=True, default={}),
        sa.Column('tool_name', sa.String(100), nullable=True),
        sa.Column('integration_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for streaming_events
    op.create_index('idx_streaming_session_time', 'streaming_events', ['session_id', 'timestamp'])
    op.create_index('idx_streaming_user_time', 'streaming_events', ['user_id', 'timestamp'])
    op.create_index('idx_streaming_type_time', 'streaming_events', ['event_type', 'timestamp'])
    op.create_index(op.f('ix_streaming_events_session_id'), 'streaming_events', ['session_id'])
    op.create_index(op.f('ix_streaming_events_user_id'), 'streaming_events', ['user_id'])
    op.create_index(op.f('ix_streaming_events_event_type'), 'streaming_events', ['event_type'])
    op.create_index(op.f('ix_streaming_events_tool_name'), 'streaming_events', ['tool_name'])
    op.create_index(op.f('ix_streaming_events_integration_id'), 'streaming_events', ['integration_id'])
    
    # Create agent_activities table
    op.create_table(
        'agent_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('processing_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('tokens_used', sa.Integer(), nullable=True, default=0),
        sa.Column('tools_called', sa.Integer(), nullable=True, default=0),
        sa.Column('input_data', sa.JSON(), nullable=True, default={}),
        sa.Column('result_data', sa.JSON(), nullable=True, default={}),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for agent_activities
    op.create_index('idx_agent_activity_agent_time', 'agent_activities', ['agent_id', 'timestamp'])
    op.create_index('idx_agent_activity_user_time', 'agent_activities', ['user_id', 'timestamp'])
    op.create_index('idx_agent_activity_session_time', 'agent_activities', ['session_id', 'timestamp'])
    op.create_index('idx_agent_activity_type_time', 'agent_activities', ['activity_type', 'timestamp'])
    op.create_index(op.f('ix_agent_activities_agent_id'), 'agent_activities', ['agent_id'])
    op.create_index(op.f('ix_agent_activities_integration_id'), 'agent_activities', ['integration_id'])
    op.create_index(op.f('ix_agent_activities_activity_type'), 'agent_activities', ['activity_type'])
    op.create_index(op.f('ix_agent_activities_session_id'), 'agent_activities', ['session_id'])
    op.create_index(op.f('ix_agent_activities_user_id'), 'agent_activities', ['user_id'])


def downgrade():
    # Drop agent_activities table and indexes
    op.drop_index(op.f('ix_agent_activities_user_id'), table_name='agent_activities')
    op.drop_index(op.f('ix_agent_activities_session_id'), table_name='agent_activities')
    op.drop_index(op.f('ix_agent_activities_activity_type'), table_name='agent_activities')
    op.drop_index(op.f('ix_agent_activities_integration_id'), table_name='agent_activities')
    op.drop_index(op.f('ix_agent_activities_agent_id'), table_name='agent_activities')
    op.drop_index('idx_agent_activity_type_time', table_name='agent_activities')
    op.drop_index('idx_agent_activity_session_time', table_name='agent_activities')
    op.drop_index('idx_agent_activity_user_time', table_name='agent_activities')
    op.drop_index('idx_agent_activity_agent_time', table_name='agent_activities')
    op.drop_table('agent_activities')
    
    # Drop streaming_events table and indexes
    op.drop_index(op.f('ix_streaming_events_integration_id'), table_name='streaming_events')
    op.drop_index(op.f('ix_streaming_events_tool_name'), table_name='streaming_events')
    op.drop_index(op.f('ix_streaming_events_event_type'), table_name='streaming_events')
    op.drop_index(op.f('ix_streaming_events_user_id'), table_name='streaming_events')
    op.drop_index(op.f('ix_streaming_events_session_id'), table_name='streaming_events')
    op.drop_index('idx_streaming_type_time', table_name='streaming_events')
    op.drop_index('idx_streaming_user_time', table_name='streaming_events')
    op.drop_index('idx_streaming_session_time', table_name='streaming_events')
    op.drop_table('streaming_events')
    
    # Drop tool_execution_events table and indexes
    op.drop_index(op.f('ix_tool_execution_events_execution_id'), table_name='tool_execution_events')
    op.drop_table('tool_execution_events')
    
    # Drop tool_executions table and indexes
    op.drop_index(op.f('ix_tool_executions_user_id'), table_name='tool_executions')
    op.drop_index(op.f('ix_tool_executions_session_id'), table_name='tool_executions')
    op.drop_index(op.f('ix_tool_executions_integration_id'), table_name='tool_executions')
    op.drop_index(op.f('ix_tool_executions_tool_name'), table_name='tool_executions')
    op.drop_index('idx_tool_execution_tool_time', table_name='tool_executions')
    op.drop_index('idx_tool_execution_integration_time', table_name='tool_executions')
    op.drop_index('idx_tool_execution_user_time', table_name='tool_executions')
    op.drop_index('idx_tool_execution_session', table_name='tool_executions')
    op.drop_table('tool_executions')