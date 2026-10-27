"""
User domain model for authentication and access control.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: Optional[int]
    username: str
    password_hash: str
    role: str  # "ADMIN" or "STAFF"
    is_active: bool = True

    @property
    def is_admin(self) -> bool:
        return self.role.upper() == "ADMIN"

    @property
    def is_staff(self) -> bool:
        return self.role.upper() == "STAFF"
