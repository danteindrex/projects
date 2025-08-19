"""Add OAuth support to integrations

Revision ID: add_oauth_support
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_oauth_support'
down_revision = None  # Update this to the current head revision
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create AuthType enum
    auth_type_enum = sa.Enum('API_KEY', 'BASIC', 'BEARER', 'OAUTH2', 'KEY_TOKEN', name='authtype')
    auth_type_enum.create(op.get_bind())
    
    # Add OAuth-related columns to integrations table
    op.add_column('integrations', sa.Column('auth_type', auth_type_enum, default='API_KEY'))
    op.add_column('integrations', sa.Column('oauth_scopes', sa.JSON(), default='[]'))
    op.add_column('integrations', sa.Column('token_expires_at', sa.DateTime(), nullable=True))
    
    # Create oauth_states table
    op.create_table('oauth_states',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('state', sa.String(length=255), nullable=False, index=True),
        sa.Column('integration_type', sa.Enum(
            'jira', 'asana', 'trello', 'monday', 'clickup',
            'zendesk', 'freshdesk', 'intercom', 'servicenow',
            'salesforce', 'hubspot', 'pipedrive', 'zoho_crm',
            'github', 'gitlab', 'bitbucket', 'azure_devops',
            'slack', 'microsoft_teams', 'discord',
            'netsuite', 'sap', 'dynamics365', 'odoo',
            'mailchimp', 'hubspot_marketing', 'marketo',
            'google_analytics', 'mixpanel',
            'aws', 'azure', 'gcp',
            'custom',
            name='integrationtype'
        ), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('integration_id', sa.Integer(), sa.ForeignKey('integrations.id'), nullable=True),
        sa.Column('client_id', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.JSON(), default='[]'),
        sa.Column('redirect_uri', sa.String(length=500)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('is_used', sa.Boolean(), default=False),
    )
    
    # Create unique constraint on state
    op.create_unique_constraint('uq_oauth_state', 'oauth_states', ['state'])
    
    # Create indexes for oauth_states
    op.create_index('idx_oauth_state_user_type', 'oauth_states', ['user_id', 'integration_type'])
    op.create_index('idx_oauth_state_expires', 'oauth_states', ['expires_at'])
    op.create_index('idx_oauth_state_used', 'oauth_states', ['is_used', 'created_at'])

def downgrade() -> None:
    # Drop oauth_states table
    op.drop_table('oauth_states')
    
    # Remove OAuth columns from integrations table
    op.drop_column('integrations', 'token_expires_at')
    op.drop_column('integrations', 'oauth_scopes')
    op.drop_column('integrations', 'auth_type')
    
    # Drop AuthType enum
    auth_type_enum = sa.Enum(name='authtype')
    auth_type_enum.drop(op.get_bind())