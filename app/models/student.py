"""
Student and Department domain models.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, Any

@dataclass
class Department:
    department_id: int
    name: str

@dataclass
class Student:
    roll_number: str
    first_name: str
    last_name: str
    date_of_birth: str  # YYYY-MM-DD
    email: str
    department_id: int
    year_level: int
    student_id: Optional[int] = None
    phone: Optional[str] = None
    gpa: Optional[float] = None
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    department_name: Optional[str] = None  # Joined display field

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert student entity to dictionary."""
        return {
            "student_id": self.student_id,
            "roll_number": self.roll_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth,
            "email": self.email,
            "phone": self.phone,
            "department_id": self.department_id,
            "department_name": self.department_name,
            "year_level": self.year_level,
            "gpa": self.gpa,
            "is_archived": self.is_archived,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Student":
        """Construct Student model from a database row (sqlite3.Row or dict)."""
        return cls(
            student_id=row["student_id"],
            roll_number=row["roll_number"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            date_of_birth=str(row["date_of_birth"]),
            email=row["email"],
            phone=row["phone"] if row["phone"] is not None else "",
            department_id=row["department_id"],
            year_level=int(row["year_level"]),
            gpa=float(row["gpa"]) if row["gpa"] is not None else None,
            is_archived=bool(row["is_archived"]),
            created_at=str(row["created_at"]) if "created_at" in row.keys() else None,
            updated_at=str(row["updated_at"]) if "updated_at" in row.keys() else None,
            department_name=row["department_name"] if "department_name" in row.keys() else None,
        )
