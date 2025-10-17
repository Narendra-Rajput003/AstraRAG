import pytest
from unittest.mock import Mock, patch
from backend.auth import (
    authenticate_user, generate_tokens, validate_invite_token,
    create_invite, register_user, setup_mfa, verify_mfa, enable_mfa
)

class TestAuthentication:
    """Test authentication functions."""

    def test_authenticate_user_success(self, test_db):
        """Test successful user authentication."""
        # Create a test user
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s)
        """, ("test@example.com", "hashed_password", "admin", True))
        test_db.commit()

        with patch('backend.auth.check_password', return_value=True):
            result = authenticate_user("test@example.com", "password123")

        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"

    def test_authenticate_user_invalid_credentials(self, test_db):
        """Test authentication with invalid credentials."""
        result = authenticate_user("nonexistent@example.com", "wrongpassword")
        assert result is None

    def test_generate_tokens(self):
        """Test JWT token generation."""
        user_data = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "role": "admin"
        }

        access_token, refresh_token = generate_tokens(user_data)

        assert access_token is not None
        assert refresh_token is not None
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)

    def test_create_invite(self, test_db):
        """Test invite creation."""
        with patch('backend.auth.secrets.token_urlsafe', return_value='test_token'):
            with patch('backend.auth.hash_password', return_value='hashed_token'):
                token = create_invite("test@example.com", "admin", "creator_id", None)

        assert token == "test_token"

        # Verify invite was created in database
        cursor = test_db.cursor()
        cursor.execute("SELECT email, role FROM invites WHERE email = %s", ("test@example.com",))
        invite = cursor.fetchone()
        assert invite is not None
        assert invite[0] == "test@example.com"
        assert invite[1] == "admin"

    def test_validate_invite_token_valid(self, test_db):
        """Test valid invite token validation."""
        # Create a test invite
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO invites (email, token_hash, role, created_by, expires_at, used)
        VALUES (%s, %s, %s, %s, NOW() + INTERVAL '1 day', %s)
        """, ("test@example.com", "hashed_token", "admin", "creator_id", False))
        test_db.commit()

        with patch('backend.auth.hash_password', return_value='hashed_token'):
            result = validate_invite_token("raw_token", "test@example.com")

        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"

    def test_validate_invite_token_expired(self, test_db):
        """Test expired invite token validation."""
        # Create an expired invite
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO invites (email, token_hash, role, created_by, expires_at, used)
        VALUES (%s, %s, %s, %s, NOW() - INTERVAL '1 day', %s)
        """, ("expired@example.com", "hashed_token", "admin", "creator_id", False))
        test_db.commit()

        with patch('backend.auth.hash_password', return_value='hashed_token'):
            with pytest.raises(Exception):  # Should raise HTTPException
                validate_invite_token("raw_token", "expired@example.com")

    def test_register_user_success(self, test_db):
        """Test successful user registration."""
        # Create a test invite
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO invites (email, token_hash, role, created_by, expires_at, used)
        VALUES (%s, %s, %s, %s, NOW() + INTERVAL '1 day', %s)
        """, ("newuser@example.com", "hashed_token", "employee", "creator_id", False))
        test_db.commit()

        with patch('backend.auth.hash_password', return_value='hashed_token'):
            with patch('backend.auth.validate_password_policy', return_value=True):
                result = register_user("newuser@example.com", "password123", "raw_token", None)

        assert result is not None
        assert result["email"] == "newuser@example.com"
        assert result["role"] == "employee"

    @patch('backend.auth.PYOTP_AVAILABLE', True)
    def test_setup_mfa_success(self, test_db):
        """Test MFA setup."""
        # Create a test user
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, %s)
        """, ("550e8400-e29b-41d4-a716-446655440000", "mfa@example.com", "hashed_password", "admin", True))
        test_db.commit()

        with patch('backend.auth.pyotp.random_base32', return_value='TESTSECRET123'):
            result = setup_mfa("550e8400-e29b-41d4-a716-446655440000")

        assert result is not None
        assert "provisioning_uri" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10

    @patch('backend.auth.PYOTP_AVAILABLE', True)
    def test_verify_mfa_success(self, test_db):
        """Test MFA verification."""
        # Create a test user with MFA secret
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, is_active, mfa_secret, backup_codes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "550e8400-e29b-41d4-a716-446655440001",
            "mfa@example.com",
            "hashed_password",
            "admin",
            True,
            "TESTSECRET123",
            ["backup1", "backup2"]
        ))
        test_db.commit()

        with patch('backend.auth.pyotp.TOTP.verify', return_value=True):
            result = verify_mfa("550e8400-e29b-41d4-a716-446655440001", "123456")

        assert result is True

    @patch('backend.auth.PYOTP_AVAILABLE', True)
    def test_verify_mfa_backup_code(self, test_db):
        """Test MFA verification with backup code."""
        # Create a test user with backup codes
        cursor = test_db.cursor()
        cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, is_active, backup_codes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            "550e8400-e29b-41d4-a716-446655440002",
            "backup@example.com",
            "hashed_password",
            "admin",
            True,
            ["backup1", "backup2", "backup3"]
        ))
        test_db.commit()

        result = verify_mfa("550e8400-e29b-41d4-a716-446655440002", "backup2")

        assert result is True

        # Verify backup code was removed
        cursor.execute("SELECT backup_codes FROM users WHERE id = %s", ("550e8400-e29b-41d4-a716-446655440002",))
        backup_codes = cursor.fetchone()[0]
        assert "backup2" not in backup_codes
        assert len(backup_codes) == 2