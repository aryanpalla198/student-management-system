"""
Data Access Object for Students, Departments, Audit Logs, and Dashboard Metrics.
Implements secure, parameterized SQL queries, connection management,
transactions, and optimistic locking.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from app.dao.db_connection import DatabaseManager, default_db_manager
from app.models.student import Department, Student
from app.utils.logger import get_logger

logger = get_logger("sms.student_dao")

# Whitelist for sort columns to prevent SQL injection in ORDER BY clauses
VALID_SORT_COLUMNS = {
    "student_id": "s.student_id",
    "roll_number": "s.roll_number",
    "first_name": "s.first_name",
    "last_name": "s.last_name",
    "department_name": "d.name",
    "year_level": "s.year_level",
    "gpa": "s.gpa",
    "created_at": "s.created_at",
    "updated_at": "s.updated_at",
}


class StudentDAO:
    """Handles all database persistence for student records and related entities."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or default_db_manager

    # -------------------------------------------------------------------------
    # Audit Logging Helper
    # -------------------------------------------------------------------------
    def log_audit(
        self,
        user_id: Optional[int],
        action: str,
        table_name: str,
        record_id: int,
        details: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Record an audit trail event inside a current or new transaction."""
        query = """
            INSERT INTO audit_log (user_id, action, table_name, record_id, details, changed_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (user_id, action, table_name, record_id, details)
        if conn is not None:
            conn.execute(query, params)
        else:
            with self.db.transaction() as c:
                c.execute(query, params)

    def get_audit_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch audit log entries with user names joined."""
        query = """
            SELECT a.log_id, a.user_id, u.username, a.action, a.table_name,
                   a.record_id, a.details, a.changed_at
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.user_id
            ORDER BY a.changed_at DESC, a.log_id DESC
            LIMIT ? OFFSET ?
        """
        with self.db.connection() as conn:
            cursor = conn.execute(query, (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # -------------------------------------------------------------------------
    # Department Operations
    # -------------------------------------------------------------------------
    def get_departments(self) -> List[Department]:
        """Fetch all departments ordered by name."""
        query = "SELECT department_id, name FROM departments ORDER BY name ASC"
        with self.db.connection() as conn:
            cursor = conn.execute(query)
            return [Department(department_id=row["department_id"], name=row["name"]) for row in cursor.fetchall()]

    def get_department_by_id(self, department_id: int) -> Optional[Department]:
        """Fetch a single department by its ID."""
        query = "SELECT department_id, name FROM departments WHERE department_id = ?"
        with self.db.connection() as conn:
            cursor = conn.execute(query, (department_id,))
            row = cursor.fetchone()
            if row:
                return Department(department_id=row["department_id"], name=row["name"])
        return None

    # -------------------------------------------------------------------------
    # Uniqueness Verification Checks
    # -------------------------------------------------------------------------
    def is_roll_number_taken(self, roll_number: str, exclude_student_id: Optional[int] = None) -> bool:
        """Check if roll number already exists, optionally excluding a student ID (for updates)."""
        if exclude_student_id:
            query = "SELECT 1 FROM students WHERE LOWER(roll_number) = LOWER(?) AND student_id != ? LIMIT 1"
            params = (roll_number.strip(), exclude_student_id)
        else:
            query = "SELECT 1 FROM students WHERE LOWER(roll_number) = LOWER(?) LIMIT 1"
            params = (roll_number.strip(),)

        with self.db.connection() as conn:
            return conn.execute(query, params).fetchone() is not None

    def is_email_taken(self, email: str, exclude_student_id: Optional[int] = None) -> bool:
        """Check if email already exists, optionally excluding a student ID."""
        if exclude_student_id:
            query = "SELECT 1 FROM students WHERE LOWER(email) = LOWER(?) AND student_id != ? LIMIT 1"
            params = (email.strip(), exclude_student_id)
        else:
            query = "SELECT 1 FROM students WHERE LOWER(email) = LOWER(?) LIMIT 1"
            params = (email.strip(),)

        with self.db.connection() as conn:
            return conn.execute(query, params).fetchone() is not None

    # -------------------------------------------------------------------------
    # Student CRUD
    # -------------------------------------------------------------------------
    def create_student(self, student: Student, user_id: Optional[int] = None) -> int:
        """
        Create a new student record within a transaction and record an audit log entry.
        Returns the newly created student_id.
        """
        query = """
            INSERT INTO students (
                roll_number, first_name, last_name, date_of_birth,
                email, phone, department_id, year_level, gpa,
                is_archived, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                0, strftime('%Y-%m-%d %H:%M:%f', 'now'), strftime('%Y-%m-%d %H:%M:%f', 'now')
            )
        """
        params = (
            student.roll_number.strip(),
            student.first_name.strip(),
            student.last_name.strip(),
            student.date_of_birth,
            student.email.strip().lower(),
            student.phone.strip() if student.phone else None,
            student.department_id,
            student.year_level,
            student.gpa,
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(query, params)
            new_id = cursor.lastrowid
            self.log_audit(
                user_id=user_id,
                action="INSERT",
                table_name="students",
                record_id=new_id,
                details=f"Created student {student.roll_number} ({student.first_name} {student.last_name})",
                conn=conn,
            )
            return new_id

    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """Fetch single student with department name by ID."""
        query = """
            SELECT s.*, d.name AS department_name
            FROM students s
            JOIN departments d ON d.department_id = s.department_id
            WHERE s.student_id = ?
        """
        with self.db.connection() as conn:
            cursor = conn.execute(query, (student_id,))
            row = cursor.fetchone()
            if row:
                return Student.from_row(dict(row))
        return None

    def get_student_by_roll_number(self, roll_number: str) -> Optional[Student]:
        """Fetch student by unique roll number."""
        query = """
            SELECT s.*, d.name AS department_name
            FROM students s
            JOIN departments d ON d.department_id = s.department_id
            WHERE LOWER(s.roll_number) = LOWER(?)
        """
        with self.db.connection() as conn:
            cursor = conn.execute(query, (roll_number.strip(),))
            row = cursor.fetchone()
            if row:
                return Student.from_row(dict(row))
        return None

    def update_student(
        self,
        student: Student,
        expected_updated_at: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Update an existing student record with optimistic locking.
        If expected_updated_at is provided, verifies that the record hasn't been modified
        by another transaction since it was read.
        """
        if not student.student_id:
            return False, "Cannot update student without student_id."

        with self.db.transaction() as conn:
            # Check current state for optimistic locking
            cursor = conn.execute(
                "SELECT updated_at, is_archived FROM students WHERE student_id = ?",
                (student.student_id,),
            )
            current = cursor.fetchone()
            if not current:
                return False, "Student record no longer exists."

            if expected_updated_at and str(current["updated_at"]) != str(expected_updated_at):
                return (
                    False,
                    "Concurrency conflict: This student record was modified by another session. Please refresh.",
                )

            update_query = """
                UPDATE students
                SET roll_number = ?,
                    first_name = ?,
                    last_name = ?,
                    date_of_birth = ?,
                    email = ?,
                    phone = ?,
                    department_id = ?,
                    year_level = ?,
                    gpa = ?,
                    updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
                WHERE student_id = ?
            """
            params = (
                student.roll_number.strip(),
                student.first_name.strip(),
                student.last_name.strip(),
                student.date_of_birth,
                student.email.strip().lower(),
                student.phone.strip() if student.phone else None,
                student.department_id,
                student.year_level,
                student.gpa,
                student.student_id,
            )

            conn.execute(update_query, params)
            self.log_audit(
                user_id=user_id,
                action="UPDATE",
                table_name="students",
                record_id=student.student_id,
                details=f"Updated student {student.roll_number} ({student.first_name} {student.last_name})",
                conn=conn,
            )

        return True, None

    def soft_delete_student(self, student_id: int, user_id: Optional[int] = None) -> bool:
        """Soft delete (archive) a student record."""
        query = """
            UPDATE students
            SET is_archived = 1,
                updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
            WHERE student_id = ?
        """
        with self.db.transaction() as conn:
            cursor = conn.execute(query, (student_id,))
            if cursor.rowcount > 0:
                self.log_audit(
                    user_id=user_id,
                    action="ARCHIVE",
                    table_name="students",
                    record_id=student_id,
                    details="Student archived (soft delete)",
                    conn=conn,
                )
                return True
        return False

    def restore_student(self, student_id: int, user_id: Optional[int] = None) -> bool:
        """Restore an archived student record to active status."""
        query = """
            UPDATE students
            SET is_archived = 0,
                updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
            WHERE student_id = ?
        """
        with self.db.transaction() as conn:
            cursor = conn.execute(query, (student_id,))
            if cursor.rowcount > 0:
                self.log_audit(
                    user_id=user_id,
                    action="RESTORE",
                    table_name="students",
                    record_id=student_id,
                    details="Student restored from archive",
                    conn=conn,
                )
                return True
        return False

    def hard_delete_student(self, student_id: int, user_id: Optional[int] = None) -> bool:
        """Permanently delete a student record (Admin only)."""
        query = "DELETE FROM students WHERE student_id = ?"
        with self.db.transaction() as conn:
            cursor = conn.execute(query, (student_id,))
            if cursor.rowcount > 0:
                self.log_audit(
                    user_id=user_id,
                    action="DELETE",
                    table_name="students",
                    record_id=student_id,
                    details="Permanently deleted student record",
                    conn=conn,
                )
                return True
        return False

    # -------------------------------------------------------------------------
    # Optimized Search, Filter, Pagination
    # -------------------------------------------------------------------------
    def search_students(
        self,
        search_query: Optional[str] = None,
        department_id: Optional[int] = None,
        year_level: Optional[int] = None,
        include_archived: bool = False,
        sort_by: str = "last_name",
        sort_dir: str = "ASC",
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Student], int]:
        """
        Search and filter students with pagination.
        Utilizes indexes on students(last_name, first_name), department_id, year_level, and is_archived.
        Returns:
            Tuple of (list_of_students, total_count)
        """
        where_clauses: List[str] = []
        params: List[Any] = []

        # Archived filter
        if not include_archived:
            where_clauses.append("s.is_archived = 0")

        # Department filter
        if department_id is not None and department_id > 0:
            where_clauses.append("s.department_id = ?")
            params.append(department_id)

        # Year level filter
        if year_level is not None and year_level > 0:
            where_clauses.append("s.year_level = ?")
            params.append(year_level)

        # Text search (roll number, first name, last name, email)
        if search_query and search_query.strip():
            sq = f"%{search_query.strip()}%"
            where_clauses.append(
                "(s.roll_number LIKE ? OR s.first_name LIKE ? OR s.last_name LIKE ? OR s.email LIKE ?)"
            )
            params.extend([sq, sq, sq, sq])

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Validate sorting
        sort_column = VALID_SORT_COLUMNS.get(sort_by, "s.last_name")
        sort_direction = "DESC" if str(sort_dir).upper() == "DESC" else "ASC"

        # Count query
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM students s
            JOIN departments d ON d.department_id = s.department_id
            {where_sql}
        """

        # Data query
        data_sql = f"""
            SELECT s.student_id, s.roll_number, s.first_name, s.last_name,
                   s.date_of_birth, s.email, s.phone, s.department_id,
                   s.year_level, s.gpa, s.is_archived, s.created_at, s.updated_at,
                   d.name AS department_name
            FROM students s
            JOIN departments d ON d.department_id = s.department_id
            {where_sql}
            ORDER BY {sort_column} {sort_direction}
            LIMIT ? OFFSET ?
        """

        with self.db.connection() as conn:
            # Get total count
            total_count = conn.execute(count_sql, params).fetchone()["total"]

            # Get paginated data
            data_params = params + [max(1, limit), max(0, offset)]
            cursor = conn.execute(data_sql, data_params)
            students = [Student.from_row(dict(row)) for row in cursor.fetchall()]

        return students, total_count

    # -------------------------------------------------------------------------
    # Dashboard Statistics
    # -------------------------------------------------------------------------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Compute aggregated statistics for dashboard views."""
        with self.db.connection() as conn:
            # Active and archived counts
            overview_row = conn.execute("""
                SELECT
                    COUNT(CASE WHEN is_archived = 0 THEN 1 END) AS active_count,
                    COUNT(CASE WHEN is_archived = 1 THEN 1 END) AS archived_count,
                    COUNT(*) AS total_count,
                    AVG(CASE WHEN is_archived = 0 AND gpa IS NOT NULL THEN gpa END) AS avg_gpa
                FROM students
            """).fetchone()

            # Department breakdown
            dept_rows = conn.execute("""
                SELECT d.name AS department,
                       COUNT(s.student_id) AS student_count,
                       ROUND(AVG(s.gpa), 2) AS avg_gpa
                FROM departments d
                LEFT JOIN students s ON s.department_id = d.department_id AND s.is_archived = 0
                GROUP BY d.department_id, d.name
                ORDER BY student_count DESC, d.name ASC
            """).fetchall()

            # Year level breakdown
            year_rows = conn.execute("""
                SELECT year_level, COUNT(*) AS student_count
                FROM students
                WHERE is_archived = 0
                GROUP BY year_level
                ORDER BY year_level ASC
            """).fetchall()

        return {
            "active_count": overview_row["active_count"] or 0,
            "archived_count": overview_row["archived_count"] or 0,
            "total_count": overview_row["total_count"] or 0,
            "avg_gpa": round(overview_row["avg_gpa"], 2) if overview_row["avg_gpa"] is not None else 0.00,
            "department_breakdown": [dict(r) for r in dept_rows],
            "year_breakdown": [dict(r) for r in year_rows],
        }
