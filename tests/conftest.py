"""
Pytest configuration and fixtures.
Provides isolated temporary SQLite database instances for DAO and Service tests.
"""

import sys
import tempfile
from pathlib import Path
import pytest

# Ensure application root is in python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import SCHEMA_PATH, SEED_PATH
from app.dao.db_connection import DatabaseManager
from app.dao.student_dao import StudentDAO
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.student_service import StudentService


@pytest.fixture
def temp_db():
    """Create a temporary on-disk SQLite database initialized with schema and seed data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)

    db_manager = DatabaseManager(temp_path)
    db_manager.init_db(SCHEMA_PATH)
    db_manager.seed_db(SEED_PATH)

    yield db_manager

    # Cleanup after test
    try:
        if temp_path.exists():
            temp_path.unlink()
    except Exception:
        pass


@pytest.fixture
def student_dao(temp_db):
    """Provide a StudentDAO connected to the temporary test database."""
    return StudentDAO(temp_db)


@pytest.fixture
def user_dao(temp_db):
    """Provide a UserDAO connected to the temporary test database."""
    return UserDAO(temp_db)


@pytest.fixture
def student_service(student_dao):
    """Provide a StudentService connected to the temporary test database."""
    return StudentService(student_dao)


@pytest.fixture
def auth_service(user_dao):
    """Provide an AuthService connected to the temporary test database."""
    return AuthService(user_dao)


@pytest.fixture
def admin_user():
    """Provide an authenticated Admin User instance."""
    return User(
        user_id=1,
        username="admin",
        password_hash="$2b$12$ud6vM.nYofPOnWOb2XtA7eg94.Sg1/Yx/ws7gk44CNzNu9rY5dyQi",
        role="ADMIN",
        is_active=True,
    )


@pytest.fixture
def staff_user():
    """Provide an authenticated Staff User instance."""
    return User(
        user_id=2,
        username="staff",
        password_hash="$2b$12$MhkZo0RVPkgJ.dt.kd.igOLU00Q8pD8GfEH65/MQVEiFuxaqKgOcq",
        role="STAFF",
        is_active=True,
    )


@pytest.fixture
def sample_student_payload():
    """Provide a valid student creation payload dictionary."""
    return {
        "roll_number": "CS9999001",
        "first_name": "Marcus",
        "last_name": "Aurelius",
        "date_of_birth": "2003-04-26",
        "email": "marcus.aurelius@university.edu",
        "phone": "+15559876",
        "department_id": 1,
        "year_level": 3,
        "gpa": 9.25,
    }
