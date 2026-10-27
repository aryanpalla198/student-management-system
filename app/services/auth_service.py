"""
Authentication and Authorization Service.
Handles bcrypt password hashing/verification, failed attempt lockouts,
and current user session management.
"""

import time
import bcrypt
from typing import Dict, Optional, Tuple
from app.config import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_SECONDS
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger("sms.auth_service")


class AuthService:
    """Provides authentication, role verification, and login rate limiting."""

    def __init__(self, user_dao: Optional[UserDAO] = None):
        self.user_dao = user_dao or UserDAO()
        # In-memory attempt tracking: username -> {"attempts": int, "lockout_until": float}
        self._login_attempts: Dict[str, Dict[str, float]] = {}
        self._current_user: Optional[User] = None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password with a unique salt using bcrypt."""
        if not password:
            raise ValueError("Password cannot be empty.")
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against bcrypt hash."""
        if not plain_password or not hashed_password:
            return False
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error("Error verifying password hash: %s", e)
            return False

    def get_lockout_remaining(self, username: str) -> int:
        """Return remaining lockout time in seconds, or 0 if not locked out."""
        uname = username.strip().lower()
        record = self._login_attempts.get(uname)
        if not record:
            return 0

        lockout_until = record.get("lockout_until", 0.0)
        now = time.time()
        if now < lockout_until:
            return int(lockout_until - now)
        return 0

    def login(self, username: str, password: str) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Authenticate user credentials.
        Returns:
            Tuple of (success, user_object_if_successful, error_message_if_failed)
        """
        if not username or not username.strip():
            return False, None, "Username is required."
        if not password:
            return False, None, "Password is required."

        uname = username.strip().lower()

        # Check if currently locked out
        remaining_lockout = self.get_lockout_remaining(uname)
        if remaining_lockout > 0:
            return (
                False,
                None,
                f"Too many failed login attempts. Account temporarily locked. Try again in {remaining_lockout} seconds.",
            )

        user = self.user_dao.get_by_username(uname)
        if not user:
            self._register_failed_attempt(uname)
            return False, None, "Invalid username or password."

        if not user.is_active:
            return False, None, "This user account has been deactivated. Please contact an Administrator."

        if not self.verify_password(password, user.password_hash):
            self._register_failed_attempt(uname)
            remaining_after = self.get_lockout_remaining(uname)
            if remaining_after > 0:
                return (
                    False,
                    None,
                    f"Too many failed attempts. Account locked for {remaining_after} seconds.",
                )
            return False, None, "Invalid username or password."

        # Successful login: reset attempts and set current user
        if uname in self._login_attempts:
            del self._login_attempts[uname]

        self._current_user = user
        logger.info("User '%s' (Role: %s) logged in successfully.", user.username, user.role)
        return True, user, None

    def _register_failed_attempt(self, uname: str) -> None:
        """Increment failed login attempts and trigger lockout if threshold reached."""
        record = self._login_attempts.setdefault(uname, {"attempts": 0, "lockout_until": 0.0})
        record["attempts"] += 1
        logger.warning("Failed login attempt #%d for user '%s'", record["attempts"], uname)

        if record["attempts"] >= MAX_LOGIN_ATTEMPTS:
            record["lockout_until"] = time.time() + LOCKOUT_DURATION_SECONDS
            record["attempts"] = 0  # Reset counter for next cycle
            logger.warning("User '%s' locked out for %d seconds", uname, LOCKOUT_DURATION_SECONDS)

    def logout(self) -> None:
        """Clear current user session."""
        if self._current_user:
            logger.info("User '%s' logged out.", self._current_user.username)
        self._current_user = None

    @property
    def current_user(self) -> Optional[User]:
        """Return the currently authenticated user, or None."""
        return self._current_user
