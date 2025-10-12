-- Initialize databases for microservices architecture
-- This script creates separate schemas/databases for each service

-- Create databases for each service
CREATE DATABASE astrarag_auth;
CREATE DATABASE astrarag_documents;
CREATE DATABASE astrarag_analytics;
CREATE DATABASE astrarag_admin;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE astrarag_auth TO astrarag;
GRANT ALL PRIVILEGES ON DATABASE astrarag_documents TO astrarag;
GRANT ALL PRIVILEGES ON DATABASE astrarag_analytics TO astrarag;
GRANT ALL PRIVILEGES ON DATABASE astrarag_admin TO astrarag;

-- Connect to auth database and create schema
\c astrarag_auth;

-- Users table for authentication service
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'employee',
    department VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR,
    backup_codes TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    refresh_token VARCHAR
);

CREATE TABLE invites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR NOT NULL,
    token_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    created_by UUID REFERENCES users(id),
    used BOOLEAN DEFAULT FALSE,
    used_by UUID REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    session_token VARCHAR UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Connect to documents database and create schema
\c astrarag_documents;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_filename VARCHAR NOT NULL,
    s3_path VARCHAR NOT NULL,
    uploaded_by UUID NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR DEFAULT 'active',
    metadata JSONB,
    file_type VARCHAR,
    file_size BIGINT,
    content_hash VARCHAR
);

CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_hash VARCHAR NOT NULL,
    changes_summary TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE document_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES document_comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author_id UUID NOT NULL,
    position_data JSONB,
    comment_type VARCHAR DEFAULT 'text',
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embed_id VARCHAR NOT NULL,
    token_count INTEGER NOT NULL
);

-- Connect to analytics database and create schema
\c astrarag_analytics;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    event_type VARCHAR NOT NULL,
    event_data JSONB,
    session_id VARCHAR,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qa_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    used_chunks JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,
    metric_value NUMERIC,
    metric_type VARCHAR NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Connect to admin database and create schema
\c astrarag_admin;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID,
    action VARCHAR NOT NULL,
    target VARCHAR,
    meta JSONB,
    ip INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_invites_email ON invites(email);
CREATE INDEX idx_invites_token_hash ON invites(token_hash);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);

CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX idx_document_versions_doc_id ON document_versions(doc_id);
CREATE INDEX idx_document_comments_doc_id ON document_comments(doc_id);
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);

CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX idx_qa_sessions_user_id ON qa_sessions(user_id);
CREATE INDEX idx_system_metrics_service ON system_metrics(service_name);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);

CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);