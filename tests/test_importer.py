"""
Unit tests for data importer and exporter utilities.
Validates CSV/Excel atomic batch processing, rollback on error, and PDF report creation.
"""

import tempfile
from pathlib import Path
import pandas as pd
import pytest
from app.utils.importer import (
    export_students_to_csv,
    export_students_to_pdf,
    import_students_from_file,
)


class TestImporterExporter:
    """Test suite for bulk import/export processing."""

    def test_import_valid_csv(self, student_dao, admin_user):
        data = [
            {
                "roll_number": "IMPORT001",
                "first_name": "Leonardo",
                "last_name": "DaVinci",
                "date_of_birth": "2002-04-15",
                "email": "leonardo@university.edu",
                "phone": "+15551111",
                "department": "Computer Science & Engineering",
                "year_level": 3,
                "gpa": 9.90,
            },
            {
                "roll_number": "IMPORT002",
                "first_name": "Galileo",
                "last_name": "Galilei",
                "date_of_birth": "2003-02-15",
                "email": "galileo@university.edu",
                "phone": "+15552222",
                "department": "Mathematics & Computing",
                "year_level": 2,
                "gpa": 9.75,
            },
        ]

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8") as f:
            temp_csv = Path(f.name)

        pd.DataFrame(data).to_csv(temp_csv, index=False)

        try:
            ok, count, errors = import_students_from_file(
                temp_csv, current_user=admin_user, student_dao=student_dao
            )
            assert ok is True
            assert count == 2
            assert len(errors) == 0

            # Verify in database
            s1 = student_dao.get_student_by_roll_number("IMPORT001")
            assert s1 is not None
            assert s1.first_name == "Leonardo"
            assert s1.gpa == 9.90
        finally:
            if temp_csv.exists():
                temp_csv.unlink()

    def test_import_rollback_on_single_invalid_row(self, student_dao, admin_user):
        # 1st row valid, 2nd row INVALID (bad email, invalid year)
        data = [
            {
                "roll_number": "ROLLOK01",
                "first_name": "Nikola",
                "last_name": "Tesla",
                "date_of_birth": "2001-07-10",
                "email": "nikola.tesla@university.edu",
                "department": "Electronics & Communication",
                "year_level": 4,
                "gpa": 9.85,
            },
            {
                "roll_number": "BAD02",  # Too short (only 5 chars min)
                "first_name": "Invalid",
                "last_name": "Row",
                "date_of_birth": "invalid-date",
                "email": "notanemail",
                "department": "Computer Science & Engineering",
                "year_level": 99,  # invalid
                "gpa": 15.0,  # invalid
            },
        ]

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8") as f:
            temp_csv = Path(f.name)

        pd.DataFrame(data).to_csv(temp_csv, index=False)

        try:
            ok, count, errors = import_students_from_file(
                temp_csv, current_user=admin_user, student_dao=student_dao
            )
            assert ok is False
            assert count == 0
            assert len(errors) > 0

            # Ensure atomic rollback: even the valid first row MUST NOT be present in database
            assert student_dao.get_student_by_roll_number("ROLLOK01") is None
        finally:
            if temp_csv.exists():
                temp_csv.unlink()

    def test_export_csv_and_pdf(self, student_dao):
        students, _ = student_dao.search_students(limit=10)
        assert len(students) > 0

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f_csv:
            csv_path = Path(f_csv.name)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f_pdf:
            pdf_path = Path(f_pdf.name)

        try:
            # Test CSV export
            out_csv = export_students_to_csv(students, csv_path)
            assert out_csv.exists()
            assert out_csv.stat().st_size > 0

            # Test PDF export
            out_pdf = export_students_to_pdf(students, pdf_path, title="Test Report")
            assert out_pdf.exists()
            assert out_pdf.stat().st_size > 0
        finally:
            if csv_path.exists():
                csv_path.unlink()
            if pdf_path.exists():
                pdf_path.unlink()
