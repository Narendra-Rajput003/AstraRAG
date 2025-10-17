import pytest
import asyncio
from typing import Generator
import psycopg2
import os
from unittest.mock import Mock, patch
from config.config import POSTGRES_URL

# Test database URL - use a separate test database
TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL", POSTGRES_URL.replace("astrarag", "astrarag_test"))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Set up test database connection."""
    # Create test database if it doesn't exist
    try:
        # Connect to default postgres database to create test database
        default_conn = psycopg2.connect(POSTGRES_URL.replace("/astrarag", "/postgres"))
        default_conn.autocommit = True
        cursor = default_conn.cursor()

        # Create test database
        cursor.execute("CREATE DATABASE astrarag_test")
        cursor.close()
        default_conn.close()
    except psycopg2.errors.DuplicateDatabase:
        pass  # Database already exists
    except Exception as e:
        print(f"Could not create test database: {e}")

    # Connect to test database
    conn = psycopg2.connect(TEST_POSTGRES_URL)
    conn.autocommit = True

    # Run migrations/schema setup
    from backend.auth import initialize_auth_db
    initialize_auth_db()

    yield conn

    # Cleanup
    conn.close()

@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    with patch('backend.api.Redis') as mock_redis:
        mock_instance = Mock()
        mock_redis.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch for testing."""
    with patch('backend.search.Elasticsearch') as mock_es:
        mock_instance = Mock()
        mock_es.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def test_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.api import app

    # Override dependencies for testing
    app.dependency_overrides = {}

    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers():
    """Generate authentication headers for testing."""
    # This would generate a valid JWT token for testing
    # For now, return a mock header
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "role": "admin",
        "organization_id": 1
    }

@pytest.fixture
def sample_document():
    """Sample document data for testing."""
    return {
        "doc_id": "550e8400-e29b-41d4-a716-446655440001",
        "filename": "test_document.pdf",
        "content": "This is test document content for testing purposes.",
        "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
        "uploaded_at": "2024-01-01T00:00:00Z",
        "file_type": "pdf",
        "file_size": 1024000,
        "status": "active",
        "metadata": {"pages": 5, "author": "Test Author"},
        "tags": ["test", "sample"]
    }