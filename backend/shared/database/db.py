import psycopg2
from config.config import POSTGRES_URL

def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(POSTGRES_URL)

def initialize_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable UUID extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR UNIQUE NOT NULL,
        password_hash VARCHAR NOT NULL,
        role VARCHAR NOT NULL DEFAULT 'employee',
        department VARCHAR,
        is_active BOOLEAN DEFAULT TRUE,
        mfa_enabled BOOLEAN DEFAULT FALSE,
        mfa_secret VARCHAR,
        backup_codes TEXT[],  -- Array of backup codes
        created_at TIMESTAMP DEFAULT NOW(),
        last_login TIMESTAMP,
        refresh_token VARCHAR
    )
    """)

    # Create invites table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR NOT NULL,
        token_hash VARCHAR NOT NULL,
        role VARCHAR NOT NULL,
        created_by UUID REFERENCES users(id),
        used BOOLEAN DEFAULT FALSE,
        used_by UUID REFERENCES users(id),
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create audit_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        actor_id UUID REFERENCES users(id),
        action VARCHAR NOT NULL,
        target VARCHAR,
        meta JSONB,
        ip INET,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        original_filename VARCHAR NOT NULL,
        s3_path VARCHAR NOT NULL,
        uploaded_by UUID REFERENCES users(id),
        uploaded_at TIMESTAMP DEFAULT NOW(),
        status VARCHAR DEFAULT 'active',
        metadata JSONB
    )
    """)

    # Create chunks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        embed_id VARCHAR NOT NULL,
        token_count INTEGER NOT NULL
    )
    """)

    # Create qa_sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qa_sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        used_chunks JSONB NOT NULL,
        timestamp TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create analytics_events table for user activity tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics_events (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        event_type VARCHAR NOT NULL,
        event_data JSONB,
        session_id VARCHAR,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create document_versions table for version tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_versions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        version_number INTEGER NOT NULL,
        content_hash VARCHAR NOT NULL,
        changes_summary TEXT,
        created_by UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create document_comments table for collaborative review
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_comments (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        parent_comment_id UUID REFERENCES document_comments(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        author_id UUID REFERENCES users(id),
        position_data JSONB,  -- For PDF/Word annotations
        comment_type VARCHAR DEFAULT 'text',  -- text, annotation, highlight
        is_resolved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create user_sessions table for session tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        session_token VARCHAR UNIQUE NOT NULL,
        ip_address INET,
        user_agent TEXT,
        started_at TIMESTAMP DEFAULT NOW(),
        ended_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    """)

    # Create system_metrics table for performance monitoring
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metrics (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        metric_type VARCHAR NOT NULL,
        metric_value NUMERIC,
        metric_unit VARCHAR,
        labels JSONB,
        recorded_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_token_hash ON invites(token_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_expires_at ON invites(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_used ON invites(used)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id ON audit_logs(actor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN (metadata)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON chunks(chunk_index)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_user_id ON qa_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_timestamp ON qa_sessions(timestamp)")

    # Create partial indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_pending_review ON documents(status) WHERE status = 'pending_review'")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(status) WHERE status = 'active'")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_active ON invites(expires_at, used) WHERE used = FALSE AND expires_at > NOW()")

    # Create composite indexes for common query patterns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by_status ON documents(uploaded_by, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at_status ON documents(uploaded_at, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_action ON audit_logs(actor_id, action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_user_timestamp ON qa_sessions(user_id, timestamp)")

    # Indexes for analytics tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_user_type ON analytics_events(user_id, event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id)")

    # Indexes for document collaboration tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_versions_doc_id ON document_versions(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON document_versions(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_doc_id ON document_comments(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_parent ON document_comments(parent_comment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_author ON document_comments(author_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_resolved ON document_comments(is_resolved)")

    # Indexes for session tracking
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active)")

    # Indexes for system metrics
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_type_time ON system_metrics(metric_type, recorded_at)")

    # Insert default superadmin user if not exists
    cursor.execute("SELECT id FROM users WHERE email='superadmin@company.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s)
        """, ("superadmin@company.com", "hashed_password_placeholder", "superadmin", True))

    conn.commit()
    conn.close()