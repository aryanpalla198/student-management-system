"""
Unit tests for AuthService.
Validates bcrypt password hashing, authentication, and lockout mechanics.
"""

import pytest


class TestAuthService:
    """Test suite for authentication, bcrypt security, and rate limiting."""

    def test_password_hashing_and_verification(self, auth_service):
        raw = "SecureSecret@123"
        hashed = auth_service.hash_password(raw)
        assert hashed != raw
        assert hashed.startswith("$2b$")
        assert auth_service.verify_password(raw, hashed) is True
        assert auth_service.verify_password("WrongPassword", hashed) is False

    def test_successful_login(self, auth_service):
        success, user, err = auth_service.login("admin", "Admin@123")
        assert success is True
        assert user is not None
        assert user.username == "admin"
        assert user.is_admin is True
        assert err is None
        assert auth_service.current_user == user

    def test_wrong_password_login(self, auth_service):
        success, user, err = auth_service.login("admin", "WrongPassword!")
        assert success is False
        assert user is None
        assert "Invalid username or password" in err

    def test_account_lockout_after_three_failed_attempts(self, auth_service):
        uname = "staff"

        # Attempt 1
        ok1, _, _ = auth_service.login(uname, "wrong1")
        assert ok1 is False
        assert auth_service.get_lockout_remaining(uname) == 0

        # Attempt 2
        ok2, _, _ = auth_service.login(uname, "wrong2")
        assert ok2 is False
        assert auth_service.get_lockout_remaining(uname) == 0

        # Attempt 3 -> Triggers lockout
        ok3, _, err3 = auth_service.login(uname, "wrong3")
        assert ok3 is False
        assert "Account locked" in err3
        assert auth_service.get_lockout_remaining(uname) > 0

        # Attempt 4 (even with CORRECT password) should be blocked by active lockout
        ok4, _, err4 = auth_service.login(uname, "Staff@123")
        assert ok4 is False
        assert "temporarily locked" in err4

    def test_logout(self, auth_service):
        auth_service.login("admin", "Admin@123")
        assert auth_service.current_user is not None
        auth_service.logout()
        assert auth_service.current_user is None
