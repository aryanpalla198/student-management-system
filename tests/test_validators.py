"""
Unit tests for data validation rules.
"""

from datetime import date
import pytest
from app.utils.validators import (
    validate_department_id,
    validate_dob,
    validate_email,
    validate_gpa,
    validate_name,
    validate_phone,
    validate_roll_number,
    validate_student_payload,
    validate_year_level,
)


class TestValidators:
    """Test suite for field-level business validation rules."""

    # Roll Number Tests
    def test_valid_roll_number(self):
        valid_rolls = ["CS2023001", "ME12345", "12345678", "A1B2C3D4E5F6G7H8"]
        for r in valid_rolls:
            ok, err = validate_roll_number(r)
            assert ok is True
            assert err is None

    def test_invalid_roll_number(self):
        invalid_rolls = ["", "   ", "CS1", "A" * 21, "CS@2023", "CS 2023", None]
        for r in invalid_rolls:
            ok, err = validate_roll_number(r)
            assert ok is False
            assert err is not None

    # Name Tests
    def test_valid_names(self):
        valid_names = ["John", "Mary-Jane", "O'Connor", "Jean Pierre", "Alexander"]
        for n in valid_names:
            ok, err = validate_name(n, "First name")
            assert ok is True
            assert err is None

    def test_invalid_names(self):
        invalid_names = ["", "   ", "John123", "Mary@Jane", "A" * 51, None]
        for n in invalid_names:
            ok, err = validate_name(n, "First name")
            assert ok is False
            assert err is not None

    # Date of Birth Tests
    def test_valid_dob(self):
        ref_date = date(2026, 1, 1)
        # 20 years old
        ok, err = validate_dob("2006-01-01", reference_date=ref_date)
        assert ok is True
        assert err is None

        # Edge cases: Exactly 15 and 60
        ok_15, _ = validate_dob("2011-01-01", reference_date=ref_date)
        assert ok_15 is True

        ok_60, _ = validate_dob("1966-01-01", reference_date=ref_date)
        assert ok_60 is True

    def test_invalid_dob(self):
        ref_date = date(2026, 1, 1)
        # Too young (14)
        ok, err = validate_dob("2012-01-01", reference_date=ref_date)
        assert ok is False
        assert "at least 15" in err

        # Too old (61)
        ok, err = validate_dob("1964-01-01", reference_date=ref_date)
        assert ok is False
        assert "not exceed 60" in err

        # Future date
        ok, err = validate_dob("2027-01-01", reference_date=ref_date)
        assert ok is False

        # Malformed strings
        for bad_date in ["not-a-date", "2000/01/01", "01-01-2000", "", None]:
            ok, err = validate_dob(bad_date, reference_date=ref_date)
            assert ok is False

    # Email Tests
    def test_valid_email(self):
        valid_emails = [
            "student@university.edu",
            "first.last@domain.co.uk",
            "user123@sub.domain.org",
        ]
        for e in valid_emails:
            ok, err = validate_email(e)
            assert ok is True
            assert err is None

    def test_invalid_email(self):
        invalid_emails = ["plainaddress", "@domain.com", "user@", "user@.com", "", "   ", None]
        for e in invalid_emails:
            ok, err = validate_email(e)
            assert ok is False
            assert err is not None

    # Phone Tests
    def test_valid_phone(self):
        valid_phones = ["+15550123", "1234567890", "+919876543210", None, "", "   "]
        for p in valid_phones:
            ok, err = validate_phone(p)
            assert ok is True

    def test_invalid_phone(self):
        invalid_phones = ["12345", "1234567890123456", "phone123", "+1-555-0123"]
        for p in invalid_phones:
            ok, err = validate_phone(p)
            assert ok is False
            assert err is not None

    # Year Level Tests
    def test_valid_year_level(self):
        for y in range(1, 7):
            ok, err = validate_year_level(y)
            assert ok is True
            ok_str, _ = validate_year_level(str(y))
            assert ok_str is True

    def test_invalid_year_level(self):
        for y in [0, 7, -1, 10, "abc", "", None]:
            ok, err = validate_year_level(y)
            assert ok is False

    # GPA Tests
    def test_valid_gpa(self):
        valid_gpas = [0.0, 5.5, 9.85, 10.0, "8.5", "0.00", "10.00", None, "", "   "]
        for g in valid_gpas:
            ok, err = validate_gpa(g)
            assert ok is True

    def test_invalid_gpa(self):
        invalid_gpas = [-0.1, 10.01, 15.0, "bad", -5]
        for g in invalid_gpas:
            ok, err = validate_gpa(g)
            assert ok is False

    # Full Payload Validation Tests
    def test_validate_student_payload_success(self, sample_student_payload):
        errors = validate_student_payload(sample_student_payload)
        assert len(errors) == 0

    def test_validate_student_payload_multiple_errors(self):
        bad_payload = {
            "roll_number": "1",  # Too short
            "first_name": "John123",  # Numbers
            "last_name": "",  # Empty
            "date_of_birth": "invalid",
            "email": "notanemail",
            "department_id": None,
            "year_level": 99,
            "gpa": 12.5,
        }
        errors = validate_student_payload(bad_payload)
        assert "roll_number" in errors
        assert "first_name" in errors
        assert "last_name" in errors
        assert "date_of_birth" in errors
        assert "email" in errors
        assert "department_id" in errors
        assert "year_level" in errors
        assert "gpa" in errors
