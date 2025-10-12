import pytest
from unittest.mock import Mock, patch
import json

class TestAPIEndpoints:
    """Test API endpoints."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
        assert "timestamp" in data

    def test_login_success(self, test_client, test_db):
        """Test successful login."""
        # Create a test user
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """, ("login@example.com", "hashed_password", "admin", True))
        user_id = cursor.fetchone()[0]
        test_db.commit()

        with patch('backend.api.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                "user_id": str(user_id),
                "email": "login@example.com",
                "role": "admin",
                "is_active": True
            }

            response = test_client.post("/auth/login", json={
                "email": "login@example.com",
                "password": "password123"
            })

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials."""
        response = test_client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401

    def test_register_user_success(self, test_client, test_db):
        """Test successful user registration."""
        # Create a test invite
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO invites (email, token_hash, role, created_by, expires_at, used)
        VALUES (%s, %s, %s, %s, NOW() + INTERVAL '1 day', %s)
        """, ("register@example.com", "hashed_token", "employee", "creator_id", False))
        test_db.commit()

        with patch('backend.api.validate_invite_token') as mock_validate:
            mock_validate.return_value = {
                "invite_id": "invite_id",
                "email": "register@example.com",
                "role": "employee",
                "created_by": "creator_id"
            }

            response = test_client.post("/auth/register", json={
                "invite_token": "test_token",
                "email": "register@example.com",
                "password": "SecurePass123!"
            })

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "user" in data

    def test_qa_query_unauthorized(self, test_client):
        """Test QA query without authentication."""
        response = test_client.post("/qa/ask", json={
            "query": "What is the company policy?"
        })

        assert response.status_code == 401

    @patch('backend.api.require_auth')
    def test_qa_query_success(self, mock_auth, test_client):
        """Test successful QA query."""
        mock_auth.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "role": "admin"
        }

        with patch('backend.api.load_and_chunk_docs', return_value=[]):
            response = test_client.post("/qa/ask", json={
                "query": "What is the company policy?"
            }, headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data

    def test_search_documents_unauthorized(self, test_client):
        """Test document search without authentication."""
        response = test_client.post("/search/documents", json={
            "query": "test query"
        })

        assert response.status_code == 401

    @patch('backend.api.require_auth')
    def test_search_documents_success(self, mock_auth, test_client, mock_elasticsearch):
        """Test successful document search."""
        mock_auth.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "role": "admin"
        }

        # Mock Elasticsearch response
        mock_search_result = {
            "documents": [
                {
                    "doc_id": "test_doc_id",
                    "filename": "test.pdf",
                    "content": "test content",
                    "uploaded_by": "user_id",
                    "uploaded_at": "2024-01-01T00:00:00Z",
                    "file_type": "pdf",
                    "file_size": 1000,
                    "status": "active",
                    "metadata": {},
                    "tags": []
                }
            ],
            "total": 1,
            "page": 1,
            "size": 20,
            "facets": {
                "file_types": ["pdf"],
                "uploaders": ["user_id"],
                "statuses": ["active"],
                "tags": [],
                "date_ranges": []
            }
        }

        with patch('backend.search.search_service.search_documents', return_value=(mock_search_result, 1)):
            response = test_client.post("/search/documents", json={
                "query": "test query"
            }, headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert len(data["documents"]) == 1

    def test_get_search_facets_unauthorized(self, test_client):
        """Test getting search facets without authentication."""
        response = test_client.get("/search/facets")

        assert response.status_code == 401

    @patch('backend.api.require_auth')
    def test_get_search_facets_success(self, mock_auth, test_client):
        """Test successful retrieval of search facets."""
        mock_auth.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "role": "admin"
        }

        with patch('backend.search.search_service.search_documents') as mock_search:
            mock_search.return_value = ({
                "facets": {
                    "file_types": ["pdf", "docx"],
                    "uploaders": ["user1", "user2"],
                    "statuses": ["active", "pending"],
                    "tags": ["policy", "hr"],
                    "date_ranges": []
                }
            }, 0)

            response = test_client.get("/search/facets", headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "file_types" in data
        assert "uploaders" in data
        assert isinstance(data["file_types"], list)

    @patch('backend.api.require_role')
    def test_admin_create_invite_success(self, mock_role, test_client):
        """Test successful admin invite creation."""
        mock_role.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "admin@example.com",
            "role": "superadmin"
        }

        with patch('backend.api.create_invite', return_value='test_invite_token'):
            response = test_client.post("/admin/invite", json={
                "email": "newuser@example.com",
                "role": "admin"
            }, headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["token"] == "test_invite_token"

    @patch('backend.api.require_role')
    def test_admin_create_invite_unauthorized(self, mock_role, test_client):
        """Test admin invite creation without proper role."""
        from fastapi import HTTPException
        mock_role.side_effect = HTTPException(status_code=403, detail="Insufficient permissions")

        response = test_client.post("/admin/invite", json={
            "email": "newuser@example.com",
            "role": "admin"
        }, headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 403

    @patch('backend.api.require_role')
    def test_get_pending_documents_success(self, mock_role, test_client, test_db):
        """Test getting pending documents."""
        mock_role.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "admin@example.com",
            "role": "superadmin"
        }

        # Create a test document
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO documents (original_filename, s3_path, uploaded_by, status, metadata)
        VALUES (%s, %s, %s, %s, %s)
        """, ("test.pdf", "/path/test.pdf", "user_id", "pending_review", {"pages": 5}))
        test_db.commit()

        response = test_client.get("/admin/documents/pending", headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0

    @patch('backend.api.require_role')
    def test_approve_document_success(self, mock_role, test_client, test_db):
        """Test successful document approval."""
        mock_role.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "admin@example.com",
            "role": "superadmin"
        }

        # Create a test document
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO documents (id, original_filename, s3_path, uploaded_by, status, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """, ("550e8400-e29b-41d4-a716-446655440001", "test.pdf", "/path/test.pdf", "user_id", "pending_review", {"pages": 5}))
        doc_id = cursor.fetchone()[0]
        test_db.commit()

        response = test_client.post("/admin/documents/approve", json={
            "doc_id": str(doc_id),
            "action": "approve"
        }, headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "approved successfully" in data["message"]

    @patch('backend.api.require_role')
    def test_security_audit_summary_success(self, mock_role, test_client):
        """Test getting security audit summary."""
        mock_role.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "admin@example.com",
            "role": "admin"
        }

        with patch('backend.security_audit.security_audit_service.run_comprehensive_security_audit') as mock_audit:
            mock_audit.return_value = {
                "overall_score": 85,
                "critical_issues": [],
                "high_issues": [{"check": "test", "severity": "high"}],
                "medium_issues": [{"check": "test2", "severity": "medium"}],
                "low_issues": [],
                "passed_checks": [{"check": "test3", "severity": "passed"}]
            }

            response = test_client.get("/admin/security-audit/summary", headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "critical_issues_count" in data
        assert data["overall_score"] == 85

    @patch('backend.api.require_role')
    def test_security_audit_full_success(self, mock_role, test_client):
        """Test running full security audit."""
        mock_role.return_value = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "admin@example.com",
            "role": "superadmin"
        }

        with patch('backend.security_audit.security_audit_service.run_comprehensive_security_audit') as mock_audit:
            mock_audit.return_value = {
                "overall_score": 90,
                "critical_issues": [],
                "high_issues": [],
                "medium_issues": [],
                "low_issues": [],
                "passed_checks": [{"check": "all_good", "severity": "passed"}],
                "recommendations": ["Keep up the good work!"]
            }

            response = test_client.get("/admin/security-audit", headers={"Authorization": "Bearer test_token"})

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "recommendations" in data
        assert data["overall_score"] == 90