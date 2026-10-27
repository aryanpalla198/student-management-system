"""
Input validation utilities for Student Management System.
Enforces business validation rules for student records and user credentials.
"""

import re
from datetime import date, datetime
from typing import Any, Dict, Optional, Tuple
from app.config import (
    MIN_STUDENT_AGE,
    MAX_STUDENT_AGE,
    MIN_YEAR_LEVEL,
    MAX_YEAR_LEVEL,
    MIN_GPA,
    MAX_GPA,
)

# Regular expressions
ROLL_NUMBER_REGEX = re.compile(r"^[A-Za-z0-9]{5,20}$")
NAME_REGEX = re.compile(r"^[A-Za-z\s'-]{1,50}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{7,15}$")


def validate_roll_number(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate roll number:
    - Required
    - 5 to 20 alphanumeric characters (no spaces or special chars)
    """
    if not value or not str(value).strip():
        return False, "Roll number is required."
    val_str = str(value).strip()
    if not ROLL_NUMBER_REGEX.match(val_str):
        return False, "Roll number must be 5 to 20 alphanumeric characters."
    return True, None


def validate_name(value: Any, field_name: str = "Name") -> Tuple[bool, Optional[str]]:
    """
    Validate student first/last name:
    - Required
    - Letters, spaces, apostrophes, hyphens only
    - Maximum 50 characters
    """
    if not value or not str(value).strip():
        return False, f"{field_name} is required."
    val_str = str(value).strip()
    if len(val_str) > 50:
        return False, f"{field_name} must not exceed 50 characters."
    if not NAME_REGEX.match(val_str):
        return False, f"{field_name} can only contain letters, spaces, hyphens, and apostrophes."
    return True, None


def validate_dob(
    value: Any, min_age: int = MIN_STUDENT_AGE, max_age: int = MAX_STUDENT_AGE, reference_date: Optional[date] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate date of birth:
    - Required
    - Valid date in YYYY-MM-DD format
    - Student age must be between min_age (15) and max_age (60)
    """
    if not value or not str(value).strip():
        return False, "Date of birth is required."
    val_str = str(value).strip()

    try:
        birth_date = datetime.strptime(val_str, "%Y-%m-%d").date()
    except ValueError:
        return False, "Date of birth must be a valid date in YYYY-MM-DD format."

    today = reference_date or date.today()
    if birth_date >= today:
        return False, "Date of birth must be in the past."

    # Exact age calculation
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    if age < min_age:
        return False, f"Student must be at least {min_age} years old (calculated age: {age})."
    if age > max_age:
        return False, f"Student age must not exceed {max_age} years old (calculated age: {age})."

    return True, None


def validate_email(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate email address:
    - Required
    - Must follow valid email format
    - Maximum 120 characters
    """
    if not value or not str(value).strip():
        return False, "Email address is required."
    val_str = str(value).strip()
    if len(val_str) > 120:
        return False, "Email address cannot exceed 120 characters."
    if not EMAIL_REGEX.match(val_str):
        return False, "Please enter a valid email address (e.g., student@domain.com)."
    return True, None


def validate_phone(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate phone number:
    - Optional
    - If provided, digits with optional leading '+', 7 to 15 digits
    """
    if value is None or str(value).strip() == "":
        return True, None  # Phone is optional
    val_str = str(value).strip()
    if not PHONE_REGEX.match(val_str):
        return False, "Phone number must be 7 to 15 digits (optional leading +)."
    return True, None


def validate_department_id(value: Any) -> Tuple[bool, Optional[str]]:
    """Validate department ID is a positive integer."""
    if value is None or str(value).strip() == "":
        return False, "Department is required."
    try:
        val_int = int(value)
        if val_int <= 0:
            return False, "Invalid department selected."
        return True, None
    except (ValueError, TypeError):
        return False, "Department ID must be a valid integer."


def validate_year_level(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate year level:
    - Required integer between MIN_YEAR_LEVEL (1) and MAX_YEAR_LEVEL (6)
    """
    if value is None or str(value).strip() == "":
        return False, "Year level is required."
    try:
        val_int = int(value)
        if not (MIN_YEAR_LEVEL <= val_int <= MAX_YEAR_LEVEL):
            return False, f"Year level must be between {MIN_YEAR_LEVEL} and {MAX_YEAR_LEVEL}."
        return True, None
    except (ValueError, TypeError):
        return False, "Year level must be an integer."


def validate_gpa(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate GPA:
    - Optional
    - If provided, decimal between MIN_GPA (0.00) and MAX_GPA (10.00)
    """
    if value is None or str(value).strip() == "":
        return True, None  # GPA is optional
    try:
        val_float = float(value)
        if not (MIN_GPA <= val_float <= MAX_GPA):
            return False, f"GPA must be between {MIN_GPA:.2f} and {MAX_GPA:.2f}."
        return True, None
    except (ValueError, TypeError):
        return False, "GPA must be a valid decimal number."


def validate_student_payload(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate all fields of a student record payload.
    Returns a dictionary of errors {field_name: error_message}.
    If valid, returns an empty dictionary.
    """
    errors: Dict[str, str] = {}

    ok, err = validate_roll_number(data.get("roll_number"))
    if not ok and err:
        errors["roll_number"] = err

    ok, err = validate_name(data.get("first_name"), "First name")
    if not ok and err:
        errors["first_name"] = err

    ok, err = validate_name(data.get("last_name"), "Last name")
    if not ok and err:
        errors["last_name"] = err

    ok, err = validate_dob(data.get("date_of_birth"))
    if not ok and err:
        errors["date_of_birth"] = err

    ok, err = validate_email(data.get("email"))
    if not ok and err:
        errors["email"] = err

    ok, err = validate_phone(data.get("phone"))
    if not ok and err:
        errors["phone"] = err

    ok, err = validate_department_id(data.get("department_id"))
    if not ok and err:
        errors["department_id"] = err

    ok, err = validate_year_level(data.get("year_level"))
    if not ok and err:
        errors["year_level"] = err

    ok, err = validate_gpa(data.get("gpa"))
    if not ok and err:
        errors["gpa"] = err

    return errors
