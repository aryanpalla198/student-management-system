"""
Integration tests for StudentDAO against temporary SQLite test database.
Validates CRUD, transactions, optimistic locking, constraints, and audit logging.
"""

import sqlite3
import time
import pytest
from app.models.student import Student


class TestStudentDAO:
    """Test suite for database persistence and querying in StudentDAO."""

    def test_create_and_get_student(self, student_dao, sample_student_payload):
        student = Student(
            roll_number=sample_student_payload["roll_number"],
            first_name=sample_student_payload["first_name"],
            last_name=sample_student_payload["last_name"],
            date_of_birth=sample_student_payload["date_of_birth"],
            email=sample_student_payload["email"],
            phone=sample_student_payload["phone"],
            department_id=sample_student_payload["department_id"],
            year_level=sample_student_payload["year_level"],
            gpa=sample_student_payload["gpa"],
        )

        new_id = student_dao.create_student(student, user_id=1)
        assert new_id > 0

        # Retrieve by ID
        fetched = student_dao.get_student_by_id(new_id)
        assert fetched is not None
        assert fetched.roll_number == "CS9999001"
        assert fetched.first_name == "Marcus"
        assert fetched.department_name is not None
        assert fetched.is_archived is False

        # Retrieve by Roll Number
        fetched_roll = student_dao.get_student_by_roll_number("CS9999001")
        assert fetched_roll is not None
        assert fetched_roll.student_id == new_id

    def test_unique_constraint_enforcement(self, student_dao, sample_student_payload):
        student = Student(
            roll_number=sample_student_payload["roll_number"],
            first_name=sample_student_payload["first_name"],
            last_name=sample_student_payload["last_name"],
            date_of_birth=sample_student_payload["date_of_birth"],
            email=sample_student_payload["email"],
            department_id=1,
            year_level=2,
        )
        student_dao.create_student(student)

        # Attempting duplicate roll number at DB level must raise IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            student_dao.create_student(student)

    def test_foreign_key_and_check_constraints(self, student_dao):
        # Invalid department (foreign key constraint)
        invalid_dept_student = Student(
            roll_number="INVALID01",
            first_name="Test",
            last_name="User",
            date_of_birth="2000-01-01",
            email="invalid.dept@university.edu",
            department_id=999999,  # Does not exist
            year_level=2,
        )
        with pytest.raises(sqlite3.IntegrityError):
            student_dao.create_student(invalid_dept_student)

        # Invalid year level (CHECK constraint)
        invalid_year_student = Student(
            roll_number="INVALID02",
            first_name="Test",
            last_name="User",
            date_of_birth="2000-01-01",
            email="invalid.year@university.edu",
            department_id=1,
            year_level=10,  # Max is 6
        )
        with pytest.raises(sqlite3.IntegrityError):
            student_dao.create_student(invalid_year_student)

    def test_optimistic_locking_update(self, student_dao, sample_student_payload):
        student = Student(
            roll_number=sample_student_payload["roll_number"],
            first_name=sample_student_payload["first_name"],
            last_name=sample_student_payload["last_name"],
            date_of_birth=sample_student_payload["date_of_birth"],
            email=sample_student_payload["email"],
            department_id=1,
            year_level=1,
            gpa=8.0,
        )
        s_id = student_dao.create_student(student)
        fetched = student_dao.get_student_by_id(s_id)
        original_updated_at = fetched.updated_at

        # Pause 10ms to ensure timestamp advances with millisecond precision
        time.sleep(0.01)

        # First update with valid updated_at
        fetched.first_name = "Marcus Updated"
        success, err = student_dao.update_student(
            fetched, expected_updated_at=original_updated_at, user_id=1
        )
        assert success is True
        assert err is None

        refreshed = student_dao.get_student_by_id(s_id)
        assert refreshed.first_name == "Marcus Updated"
        new_updated_at = refreshed.updated_at
        assert new_updated_at != original_updated_at

        # Second update with STALE timestamp (original_updated_at is now stale)
        refreshed.first_name = "Conflict Update"
        success_conflict, err_conflict = student_dao.update_student(
            refreshed, expected_updated_at=original_updated_at, user_id=1
        )
        assert success_conflict is False
        assert "Concurrency conflict" in err_conflict

    def test_soft_delete_and_restore(self, student_dao):
        # Alice Smith is seeded at student_id=1
        student = student_dao.get_student_by_id(1)
        assert student.is_archived is False

        # Soft delete (archive)
        ok = student_dao.soft_delete_student(1, user_id=1)
        assert ok is True

        archived_student = student_dao.get_student_by_id(1)
        assert archived_student.is_archived is True

        # Restore
        ok_restore = student_dao.restore_student(1, user_id=1)
        assert ok_restore is True

        restored_student = student_dao.get_student_by_id(1)
        assert restored_student.is_archived is False

    def test_hard_delete(self, student_dao, sample_student_payload):
        student = Student(
            roll_number="DELETE_ME",
            first_name="Temp",
            last_name="Record",
            date_of_birth="2000-01-01",
            email="delete.me@university.edu",
            department_id=1,
            year_level=1,
        )
        s_id = student_dao.create_student(student)
        assert student_dao.get_student_by_id(s_id) is not None

        # Hard delete
        ok = student_dao.hard_delete_student(s_id, user_id=1)
        assert ok is True
        assert student_dao.get_student_by_id(s_id) is None

    def test_paginated_search(self, student_dao):
        # Search by query "Alice"
        results, total = student_dao.search_students(search_query="Alice", limit=5, offset=0)
        assert total >= 1
        assert any("Alice" in s.first_name for s in results)

        # Filter by department (CS is id 1)
        cs_results, cs_total = student_dao.search_students(department_id=1, limit=5, offset=0)
        assert cs_total > 0
        assert all(s.department_id == 1 for s in cs_results)

        # Pagination: 15 seeded students, limit 5
        page1, _ = student_dao.search_students(limit=5, offset=0)
        page2, _ = student_dao.search_students(limit=5, offset=5)
        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0].student_id != page2[0].student_id

    def test_audit_logging(self, student_dao):
        logs = student_dao.get_audit_logs(limit=20)
        assert len(logs) > 0
        actions = [l["action"] for l in logs]
        assert "SEED" in actions or "INSERT" in actions
