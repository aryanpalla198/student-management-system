"""
Services package initialization.
"""
from app.services.auth_service import AuthService
from app.services.student_service import StudentService

__all__ = ["AuthService", "StudentService"]
