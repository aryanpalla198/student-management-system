"""
Import and Export utility for Student Records.
Supports CSV and Excel import with atomic transactional validation,
and CSV / PDF export with ReportLab.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from app.dao.student_dao import StudentDAO
from app.models.student import Student
from app.models.user import User
from app.utils.logger import get_logger
from app.utils.validators import validate_student_payload

logger = get_logger("sms.importer")


def import_students_from_file(
    file_path: Path,
    current_user: Optional[User] = None,
    student_dao: Optional[StudentDAO] = None,
) -> Tuple[bool, int, List[str]]:
    """
    Read students from CSV or Excel file and import them atomically.
    Validates all rows before inserting anything. If any row fails,
    aborts the entire transaction and returns an error list.

    Returns:
        Tuple of (success, count_imported, list_of_error_messages)
    """
    dao = student_dao or StudentDAO()
    file_path = Path(file_path)

    if not file_path.exists():
        return False, 0, [f"File not found: {file_path}"]

    # 1. Read file into DataFrame
    try:
        suffix = file_path.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        elif suffix == ".csv":
            df = pd.read_csv(file_path)
        else:
            return False, 0, [f"Unsupported file format '{suffix}'. Supported formats are .csv, .xlsx, .xls"]
    except Exception as e:
        logger.error("Failed to read import file %s: %s", file_path, e)
        return False, 0, [f"Error reading file: {str(e)}"]

    if df.empty:
        return False, 0, ["The selected file is empty."]

    # Normalize column names: strip and lowercase
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Map possible column header variations
    col_mapping = {
        "roll_no": "roll_number",
        "roll": "roll_number",
        "dob": "date_of_birth",
        "birth_date": "date_of_birth",
        "dept": "department",
        "department_name": "department",
        "year": "year_level",
        "first": "first_name",
        "last": "last_name",
    }
    df = df.rename(columns=col_mapping)

    # Department lookup map: name -> id and id -> id
    departments = dao.get_departments()
    dept_name_to_id = {d.name.lower(): d.department_id for d in departments}
    dept_id_set = {d.department_id for d in departments}

    errors: List[str] = []
    students_to_insert: List[Student] = []
    seen_roll_numbers = set()
    seen_emails = set()

    # 2. Validate every row
    for index, row in df.iterrows():
        row_num = index + 2  # 1-based index plus header row

        # Resolve department ID
        dept_val = row.get("department_id") or row.get("department")
        dept_id = None
        if pd.notna(dept_val):
            # Check if integer ID directly
            try:
                cand_id = int(dept_val)
                if cand_id in dept_id_set:
                    dept_id = cand_id
            except (ValueError, TypeError):
                pass

            if dept_id is None:
                # Try matching by name
                dept_str = str(dept_val).strip().lower()
                dept_id = dept_name_to_id.get(dept_str)

        raw_phone = str(row.get("phone", "")).strip() if pd.notna(row.get("phone")) else None
        if raw_phone and raw_phone.endswith(".0"):  # Handle float formatting in excel
            raw_phone = raw_phone[:-2]

        raw_gpa = row.get("gpa")
        gpa_val = None
        if pd.notna(raw_gpa) and str(raw_gpa).strip() != "":
            try:
                gpa_val = float(raw_gpa)
            except ValueError:
                errors.append(f"Row {row_num}: GPA '{raw_gpa}' is not a valid number.")

        raw_dob = row.get("date_of_birth")
        dob_str = ""
        if pd.notna(raw_dob):
            if isinstance(raw_dob, (datetime, pd.Timestamp)):
                dob_str = raw_dob.strftime("%Y-%m-%d")
            else:
                dob_str = str(raw_dob).strip()

        payload = {
            "roll_number": str(row.get("roll_number", "")).strip() if pd.notna(row.get("roll_number")) else "",
            "first_name": str(row.get("first_name", "")).strip() if pd.notna(row.get("first_name")) else "",
            "last_name": str(row.get("last_name", "")).strip() if pd.notna(row.get("last_name")) else "",
            "date_of_birth": dob_str,
            "email": str(row.get("email", "")).strip().lower() if pd.notna(row.get("email")) else "",
            "phone": raw_phone,
            "department_id": dept_id,
            "year_level": row.get("year_level"),
            "gpa": gpa_val,
        }

        # Validate fields
        field_errs = validate_student_payload(payload)
        for field, err in field_errs.items():
            errors.append(f"Row {row_num} [{field}]: {err}")

        # Check in-file duplicates
        roll_num = payload["roll_number"]
        if roll_num:
            if roll_num.lower() in seen_roll_numbers:
                errors.append(f"Row {row_num}: Duplicate roll number '{roll_num}' found within the import file.")
            seen_roll_numbers.add(roll_num.lower())

            # Check database duplicate
            if dao.is_roll_number_taken(roll_num):
                errors.append(f"Row {row_num}: Roll number '{roll_num}' already exists in database.")

        email_val = payload["email"]
        if email_val:
            if email_val in seen_emails:
                errors.append(f"Row {row_num}: Duplicate email '{email_val}' found within the import file.")
            seen_emails.add(email_val)

            # Check database duplicate
            if dao.is_email_taken(email_val):
                errors.append(f"Row {row_num}: Email '{email_val}' already exists in database.")

        if not errors:
            students_to_insert.append(
                Student(
                    roll_number=payload["roll_number"],
                    first_name=payload["first_name"],
                    last_name=payload["last_name"],
                    date_of_birth=payload["date_of_birth"],
                    email=payload["email"],
                    phone=payload["phone"],
                    department_id=payload["department_id"],
                    year_level=int(payload["year_level"]),
                    gpa=payload["gpa"],
                )
            )

    # 3. If any error was collected, abort import
    if errors:
        logger.warning("Import aborted due to %d validation errors.", len(errors))
        return False, 0, errors

    # 4. Insert all valid students in a single atomic transaction
    user_id = current_user.user_id if current_user else None
    inserted_count = 0

    with dao.db.transaction() as conn:
        for student in students_to_insert:
            query = """
                INSERT INTO students (
                    roll_number, first_name, last_name, date_of_birth,
                    email, phone, department_id, year_level, gpa,
                    is_archived, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, strftime('%Y-%m-%d %H:%M:%f', 'now'), strftime('%Y-%m-%d %H:%M:%f', 'now'))
            """
            cursor = conn.execute(
                query,
                (
                    student.roll_number,
                    student.first_name,
                    student.last_name,
                    student.date_of_birth,
                    student.email,
                    student.phone,
                    student.department_id,
                    student.year_level,
                    student.gpa,
                ),
            )
            dao.log_audit(
                user_id=user_id,
                action="IMPORT",
                table_name="students",
                record_id=cursor.lastrowid,
                details=f"Bulk imported student {student.roll_number}",
                conn=conn,
            )
            inserted_count += 1

    logger.info("Successfully imported %d students from %s", inserted_count, file_path)
    return True, inserted_count, []


def export_students_to_csv(students: List[Student], output_file: Path) -> Path:
    """Export a list of students to a CSV file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for s in students:
        rows.append({
            "Student ID": s.student_id,
            "Roll Number": s.roll_number,
            "First Name": s.first_name,
            "Last Name": s.last_name,
            "Date of Birth": s.date_of_birth,
            "Email": s.email,
            "Phone": s.phone or "",
            "Department": s.department_name or "",
            "Year Level": s.year_level,
            "GPA": f"{s.gpa:.2f}" if s.gpa is not None else "",
            "Status": "Archived" if s.is_archived else "Active",
            "Created At": s.created_at or "",
            "Updated At": s.updated_at or "",
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Exported %d students to CSV: %s", len(students), output_path)
    return output_path


def export_students_to_pdf(students: List[Student], output_file: Path, title: str = "Student Records Report") -> Path:
    """Generate a formatted PDF report of students using ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(letter),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14,
    )

    story = []

    # Title & Generation Metadata
    story.append(Paragraph(title, title_style))
    meta_text = (
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Total Records: {len(students)} | Institutional Confidential"
    )
    story.append(Paragraph(meta_text, meta_style))

    # Table Header and Rows
    header = ["Roll No", "Name", "Department", "Year", "GPA", "Email", "Phone", "Status"]
    table_data = [header]

    for s in students:
        table_data.append([
            s.roll_number,
            f"{s.first_name} {s.last_name}",
            (s.department_name or "N/A")[:24],
            f"Year {s.year_level}",
            f"{s.gpa:.2f}" if s.gpa is not None else "N/A",
            s.email,
            s.phone or "-",
            "Archived" if s.is_archived else "Active",
        ])

    table = Table(
        table_data,
        colWidths=[70, 110, 140, 50, 45, 170, 85, 60],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (3, 0), (4, -1), "CENTER"),  # Year and GPA centered
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#F8FAFC")],
            ),
        ])
    )

    story.append(table)
    doc.build(story)
    logger.info("Exported %d students to PDF: %s", len(students), output_path)
    return output_path
