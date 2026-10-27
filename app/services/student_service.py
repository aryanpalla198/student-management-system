"""
Student Business Logic Service.
Enforces business rules, duplicate detection, field validation,
optimistic locking, and role-based permissions.
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.dao.student_dao import StudentDAO
from app.models.student import Department, Student
from app.models.user import User
from app.utils.logger import get_logger
from app.utils.validators import validate_student_payload

logger = get_logger("sms.student_service")


class StudentService:
    """Coordinates student CRUD operations, business rules, and permissions."""

    def __init__(self, student_dao: Optional[StudentDAO] = None):
        self.student_dao = student_dao or StudentDAO()

    # -------------------------------------------------------------------------
    # Read & Search Operations
    # -------------------------------------------------------------------------
    def get_student(self, student_id: int) -> Optional[Student]:
        """Fetch student by ID."""
        return self.student_dao.get_student_by_id(student_id)

    def get_student_by_roll(self, roll_number: str) -> Optional[Student]:
        """Fetch student by roll number."""
        return self.student_dao.get_student_by_roll_number(roll_number)

    def get_departments(self) -> List[Department]:
        """Get list of all academic departments."""
        return self.student_dao.get_departments()

    def search_students(
        self,
        query: Optional[str] = None,
        department_id: Optional[int] = None,
        year_level: Optional[int] = None,
        include_archived: bool = False,
        sort_by: str = "last_name",
        sort_dir: str = "ASC",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Student], int, int]:
        """
        Search students with sorting and pagination.
        Returns:
            Tuple of (students_list, total_records, total_pages)
        """
        page = max(1, page)
        page_size = max(1, page_size)
        offset = (page - 1) * page_size

        students, total_count = self.student_dao.search_students(
            search_query=query,
            department_id=department_id,
            year_level=year_level,
            include_archived=include_archived,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=page_size,
            offset=offset,
        )

        total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1
        return students, total_count, total_pages

    # -------------------------------------------------------------------------
    # Create Operation
    # -------------------------------------------------------------------------
    def create_student(
        self, data: Dict[str, Any], current_user: Optional[User] = None
    ) -> Tuple[bool, Optional[Student], Optional[Dict[str, str]]]:
        """
        Validate, verify uniqueness, and persist a new student.
        Returns:
            Tuple of (success, created_student, validation_errors_dict)
        """
        errors = validate_student_payload(data)

        # Verify department existence
        dept_id = data.get("department_id")
        if dept_id and not errors.get("department_id"):
            dept = self.student_dao.get_department_by_id(int(dept_id))
            if not dept:
                errors["department_id"] = "Selected department does not exist."

        # Check unique constraints
        roll_num = str(data.get("roll_number", "")).strip()
        if roll_num and not errors.get("roll_number"):
            if self.student_dao.is_roll_number_taken(roll_num):
                errors["roll_number"] = f"A student with roll number '{roll_num}' already exists."

        email = str(data.get("email", "")).strip().lower()
        if email and not errors.get("email"):
            if self.student_dao.is_email_taken(email):
                errors["email"] = f"A student with email '{email}' already exists."

        if errors:
            logger.warning("Student creation validation failed: %s", errors)
            return False, None, errors

        # Convert GPA to float if provided
        gpa_val = None
        if data.get("gpa") is not None and str(data.get("gpa")).strip() != "":
            gpa_val = float(data.get("gpa"))

        student = Student(
            roll_number=roll_num,
            first_name=str(data.get("first_name", "")).strip(),
            last_name=str(data.get("last_name", "")).strip(),
            date_of_birth=str(data.get("date_of_birth", "")).strip(),
            email=email,
            phone=str(data.get("phone", "")).strip() if data.get("phone") else None,
            department_id=int(data["department_id"]),
            year_level=int(data["year_level"]),
            gpa=gpa_val,
        )

        user_id = current_user.user_id if current_user else None
        student_id = self.student_dao.create_student(student, user_id=user_id)
        created_student = self.student_dao.get_student_by_id(student_id)

        logger.info("Student #%d ('%s') created successfully by user %s.", student_id, roll_num, user_id)
        return True, created_student, None

    # -------------------------------------------------------------------------
    # Update Operation with Optimistic Concurrency Control
    # -------------------------------------------------------------------------
    def update_student(
        self,
        student_id: int,
        data: Dict[str, Any],
        expected_updated_at: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> Tuple[bool, Optional[Student], Optional[Dict[str, str]]]:
        """
        Validate, check uniqueness, check optimistic locking, and update student.
        Returns:
            Tuple of (success, updated_student, validation_errors_dict)
        """
        existing = self.student_dao.get_student_by_id(student_id)
        if not existing:
            return False, None, {"general": f"Student with ID {student_id} not found."}

        errors = validate_student_payload(data)

        # Department check
        dept_id = data.get("department_id")
        if dept_id and not errors.get("department_id"):
            dept = self.student_dao.get_department_by_id(int(dept_id))
            if not dept:
                errors["department_id"] = "Selected department does not exist."

        # Unique checks excluding current student_id
        roll_num = str(data.get("roll_number", "")).strip()
        if roll_num and not errors.get("roll_number"):
            if self.student_dao.is_roll_number_taken(roll_num, exclude_student_id=student_id):
                errors["roll_number"] = f"Roll number '{roll_num}' is already in use by another student."

        email = str(data.get("email", "")).strip().lower()
        if email and not errors.get("email"):
            if self.student_dao.is_email_taken(email, exclude_student_id=student_id):
                errors["email"] = f"Email '{email}' is already in use by another student."

        if errors:
            logger.warning("Student update validation failed for ID %d: %s", student_id, errors)
            return False, None, errors

        # Convert GPA
        gpa_val = None
        if data.get("gpa") is not None and str(data.get("gpa")).strip() != "":
            gpa_val = float(data.get("gpa"))

        updated_entity = Student(
            student_id=student_id,
            roll_number=roll_num,
            first_name=str(data.get("first_name", "")).strip(),
            last_name=str(data.get("last_name", "")).strip(),
            date_of_birth=str(data.get("date_of_birth", "")).strip(),
            email=email,
            phone=str(data.get("phone", "")).strip() if data.get("phone") else None,
            department_id=int(data["department_id"]),
            year_level=int(data["year_level"]),
            gpa=gpa_val,
        )

        user_id = current_user.user_id if current_user else None
        success, conflict_err = self.student_dao.update_student(
            updated_entity,
            expected_updated_at=expected_updated_at,
            user_id=user_id,
        )

        if not success:
            return False, None, {"general": conflict_err or "Failed to update student record."}

        refreshed = self.student_dao.get_student_by_id(student_id)
        logger.info("Student #%d ('%s') updated successfully by user %s.", student_id, roll_num, user_id)
        return True, refreshed, None

    # -------------------------------------------------------------------------
    # Delete & Archive with Role-Based Permission Control
    # -------------------------------------------------------------------------
    def delete_student(
        self,
        student_id: int,
        permanent: bool = False,
        current_user: Optional[User] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete student.
        - Soft delete (archive): Permitted for all authenticated staff and admins.
        - Permanent delete (hard): Permitted strictly for ADMIN role.
        """
        existing = self.student_dao.get_student_by_id(student_id)
        if not existing:
            return False, f"Student #{student_id} not found."

        user_id = current_user.user_id if current_user else None

        if permanent:
            # Enforce ADMIN role requirement for permanent deletion
            if not current_user or not current_user.is_admin:
                logger.warning(
                    "Unauthorized hard delete attempt on student #%d by user %s",
                    student_id,
                    current_user.username if current_user else "Anonymous",
                )
                return False, "Permission denied: Permanent record deletion requires Administrator privileges."

            ok = self.student_dao.hard_delete_student(student_id, user_id=user_id)
            if ok:
                logger.info("Student #%d permanently deleted by admin %s.", student_id, user_id)
                return True, None
            return False, "Database error: Could not permanently delete student."

        else:
            # Soft delete (archive)
            ok = self.student_dao.soft_delete_student(student_id, user_id=user_id)
            if ok:
                logger.info("Student #%d archived by user %s.", student_id, user_id)
                return True, None
            return False, "Database error: Could not archive student."

    def restore_student(
        self, student_id: int, current_user: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        """Restore an archived student back to active status."""
        existing = self.student_dao.get_student_by_id(student_id)
        if not existing:
            return False, f"Student #{student_id} not found."

        user_id = current_user.user_id if current_user else None
        ok = self.student_dao.restore_student(student_id, user_id=user_id)
        if ok:
            logger.info("Student #%d restored by user %s.", student_id, user_id)
            return True, None
        return False, "Database error: Could not restore student."

    # -------------------------------------------------------------------------
    # Dashboard, Audit Logs, and Backup
    # -------------------------------------------------------------------------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Fetch real-time dashboard statistics and metrics."""
        return self.student_dao.get_dashboard_stats()

    def get_audit_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch audit log records."""
        return self.student_dao.get_audit_logs(limit=limit, offset=offset)

    def create_database_backup(self) -> Path:
        """Trigger an online database backup and return the backup file path."""
        return self.student_dao.db.backup_db()
