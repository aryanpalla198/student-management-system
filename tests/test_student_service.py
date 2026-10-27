"""
Unit and integration tests for StudentService.
Validates business logic, duplicate detection, optimistic locking,
and role-based authorization.
"""

import pytest


class TestStudentService:
    """Test suite for StudentService business rules and security policies."""

    def test_create_student_success(self, student_service, admin_user, sample_student_payload):
        success, student, errors = student_service.create_student(
            sample_student_payload, current_user=admin_user
        )
        assert success is True
        assert student is not None
        assert errors is None
        assert student.roll_number == "CS9999001"

    def test_create_duplicate_roll_number(self, student_service, admin_user, sample_student_payload):
        # First creation succeeds
        student_service.create_student(sample_student_payload, current_user=admin_user)

        # Second creation with identical roll number must fail
        duplicate_payload = sample_student_payload.copy()
        duplicate_payload["email"] = "different.email@university.edu"

        success, student, errors = student_service.create_student(
            duplicate_payload, current_user=admin_user
        )
        assert success is False
        assert student is None
        assert "roll_number" in errors
        assert "already exists" in errors["roll_number"]

    def test_create_duplicate_email(self, student_service, admin_user, sample_student_payload):
        student_service.create_student(sample_student_payload, current_user=admin_user)

        # Second creation with different roll number but same email
        duplicate_payload = sample_student_payload.copy()
        duplicate_payload["roll_number"] = "CS8888002"

        success, student, errors = student_service.create_student(
            duplicate_payload, current_user=admin_user
        )
        assert success is False
        assert "email" in errors
        assert "already exists" in errors["email"]

    def test_update_student_success(self, student_service, admin_user, sample_student_payload):
        _, created, _ = student_service.create_student(sample_student_payload, current_user=admin_user)

        update_payload = sample_student_payload.copy()
        update_payload["first_name"] = "Lucius"
        update_payload["gpa"] = 9.80

        success, updated, errors = student_service.update_student(
            student_id=created.student_id,
            data=update_payload,
            expected_updated_at=created.updated_at,
            current_user=admin_user,
        )
        assert success is True
        assert updated.first_name == "Lucius"
        assert updated.gpa == 9.80

    def test_role_based_deletion_rules(self, student_service, staff_user, admin_user, sample_student_payload):
        # 1. Staff can perform soft delete (archive)
        _, s1, _ = student_service.create_student(sample_student_payload, current_user=staff_user)
        ok_archive, err_archive = student_service.delete_student(
            s1.student_id, permanent=False, current_user=staff_user
        )
        assert ok_archive is True
        assert err_archive is None

        # 2. Staff is REJECTED when attempting permanent delete
        ok_hard_staff, err_hard_staff = student_service.delete_student(
            s1.student_id, permanent=True, current_user=staff_user
        )
        assert ok_hard_staff is False
        assert "requires Administrator privileges" in err_hard_staff

        # 3. Admin is ALLOWED to perform permanent delete
        ok_hard_admin, err_hard_admin = student_service.delete_student(
            s1.student_id, permanent=True, current_user=admin_user
        )
        assert ok_hard_admin is True
        assert err_hard_admin is None

    def test_search_and_pagination_calculations(self, student_service):
        students, total_records, total_pages = student_service.search_students(
            page=1, page_size=5
        )
        assert total_records >= 14
        assert total_pages >= 3
        assert len(students) == 5

    def test_dashboard_stats(self, student_service):
        stats = student_service.get_dashboard_stats()
        assert stats["total_count"] >= 15
        assert stats["active_count"] >= 14
        assert stats["avg_gpa"] > 0
        assert len(stats["department_breakdown"]) > 0

    def test_get_student_and_departments(self, student_service):
        # By ID
        s = student_service.get_student(1)
        assert s is not None
        assert s.student_id == 1

        # By Roll
        s_roll = student_service.get_student_by_roll(s.roll_number)
        assert s_roll is not None
        assert s_roll.roll_number == s.roll_number

        # Departments
        depts = student_service.get_departments()
        assert len(depts) >= 6

    def test_restore_student(self, student_service, admin_user):
        # Soft delete first
        student_service.delete_student(1, permanent=False, current_user=admin_user)
        assert student_service.get_student(1).is_archived is True

        # Restore
        ok, err = student_service.restore_student(1, current_user=admin_user)
        assert ok is True
        assert err is None
        assert student_service.get_student(1).is_archived is False

    def test_create_database_backup(self, student_service):
        backup_file = student_service.create_database_backup()
        assert backup_file.exists()
        assert backup_file.stat().st_size > 0
        try:
            backup_file.unlink()
        except Exception:
            pass
