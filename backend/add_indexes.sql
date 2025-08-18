-- Database indexes for improved query performance
-- Run this script after creating tables

-- User table indexes (email and username already have unique indexes)
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);

-- Integration table indexes
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);
CREATE INDEX IF NOT EXISTS idx_integrations_owner_id ON integrations(owner_id);
CREATE INDEX IF NOT EXISTS idx_integrations_tenant_id ON integrations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_integrations_created_at ON integrations(created_at);
CREATE INDEX IF NOT EXISTS idx_integrations_health_status ON integrations(health_status);
CREATE INDEX IF NOT EXISTS idx_integrations_last_health_check ON integrations(last_health_check);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_integrations_owner_status ON integrations(owner_id, status);
CREATE INDEX IF NOT EXISTS idx_integrations_tenant_type ON integrations(tenant_id, integration_type);

-- Chat session indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant_id ON chat_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);

-- Chat message indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_chat_messages_tenant_id ON chat_messages(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_status ON chat_messages(tool_status);

-- Composite indexes for chat queries
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_tenant_session ON chat_messages(tenant_id, session_id);

-- Agent table indexes (if exists)
-- CREATE INDEX IF NOT EXISTS idx_agents_integration_id ON agents(integration_id);
-- CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
-- CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
-- CREATE INDEX IF NOT EXISTS idx_agents_tenant_id ON agents(tenant_id);

-- Performance analysis queries to test index effectiveness:
-- EXPLAIN QUERY PLAN SELECT * FROM integrations WHERE owner_id = ? AND status = 'active';
-- EXPLAIN QUERY PLAN SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at DESC LIMIT 50;
-- EXPLAIN QUERY PLAN SELECT * FROM integrations WHERE integration_type = 'jira' AND health_status = 'healthy';