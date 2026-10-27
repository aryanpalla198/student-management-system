"""
Data Access Object for User operations (Authentication & Authorization).
"""

from typing import List, Optional
from app.dao.db_connection import DatabaseManager, default_db_manager
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger("sms.user_dao")


class UserDAO:
    """Handles database persistence and queries for User records."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or default_db_manager

    def get_by_username(self, username: str) -> Optional[User]:
        """Fetch user by case-insensitive username."""
        query = """
            SELECT user_id, username, password_hash, role, is_active
            FROM users
            WHERE LOWER(username) = LOWER(?)
        """
        with self.db.connection() as conn:
            cursor = conn.execute(query, (username.strip(),))
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row["user_id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    is_active=bool(row["is_active"]),
                )
        return None

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by primary key."""
        query = """
            SELECT user_id, username, password_hash, role, is_active
            FROM users
            WHERE user_id = ?
        """
        with self.db.connection() as conn:
            cursor = conn.execute(query, (user_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row["user_id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    is_active=bool(row["is_active"]),
                )
        return None

    def create_user(self, username: str, password_hash: str, role: str) -> int:
        """Create a new user record."""
        query = """
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, 1)
        """
        with self.db.transaction() as conn:
            cursor = conn.execute(query, (username.strip(), password_hash, role.upper()))
            return cursor.lastrowid

    def list_users(self) -> List[User]:
        """List all users."""
        query = """
            SELECT user_id, username, password_hash, role, is_active
            FROM users
            ORDER BY username ASC
        """
        users = []
        with self.db.connection() as conn:
            cursor = conn.execute(query)
            for row in cursor.fetchall():
                users.append(
                    User(
                        user_id=row["user_id"],
                        username=row["username"],
                        password_hash=row["password_hash"],
                        role=row["role"],
                        is_active=bool(row["is_active"]),
                    )
                )
        return users
