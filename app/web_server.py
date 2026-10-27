"""
FastAPI Web Server for AcademiaSMS.
Exposes RESTful endpoints connecting to the StudentService and DAO layers,
and serves the single-page application for Google Chrome.
"""

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.dao.db_connection import default_db_manager
from app.dao.student_dao import StudentDAO
from app.dao.user_dao import UserDAO
from app.main import ensure_database_ready
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.student_service import StudentService
from app.utils.importer import (
    export_students_to_csv,
    export_students_to_pdf,
    import_students_from_file,
)
from app.utils.logger import get_logger

logger = get_logger("sms.web_server")

# Ensure database is initialized with seeds
ensure_database_ready()

app = FastAPI(
    title="AcademiaSMS Web API",
    description="Enterprise Student Management System REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

student_dao = StudentDAO(default_db_manager)
user_dao = UserDAO(default_db_manager)
auth_service = AuthService(user_dao)
student_service = StudentService(student_dao)

# Default admin session user for local web console
web_admin_user = User(
    user_id=1,
    username="admin",
    password_hash="",
    role="ADMIN",
    is_active=True,
)

WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_FILE = WEB_DIR / "index.html"


# Pydantic Schemas
class StudentPayload(BaseModel):
    roll_number: str
    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    phone: Optional[str] = None
    department_id: int
    year_level: int
    gpa: Optional[float] = None
    expected_updated_at: Optional[str] = None


@app.get("/")
async def serve_index():
    """Serve the modern web dashboard interface."""
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Web interface index.html not found.")
    return FileResponse(INDEX_FILE, media_type="text/html")


@app.get("/api/departments")
async def get_departments():
    """List all registered academic departments."""
    depts = student_service.get_departments()
    return [{"department_id": d.department_id, "name": d.name} for d in depts]


@app.get("/api/students")
async def list_students(
    query: Optional[str] = None,
    department_id: Optional[int] = None,
    year_level: Optional[int] = None,
    include_archived: bool = False,
    sort_by: str = "last_name",
    sort_dir: str = "ASC",
    page: int = 1,
    page_size: int = 10,
):
    """Retrieve filtered, sorted, and paginated student records."""
    students, total_records, total_pages = student_service.search_students(
        query=query,
        department_id=department_id,
        year_level=year_level,
        include_archived=include_archived,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return {
        "students": [s.to_dict() for s in students],
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
    }


@app.post("/api/students")
async def create_student(payload: StudentPayload):
    """Create a new student record with business and uniqueness validation."""
    success, created, errors = student_service.create_student(
        payload.model_dump(), current_user=web_admin_user
    )
    if not success:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": errors},
        )
    return {"success": True, "student": created.to_dict()}


@app.get("/api/students/{student_id}")
async def get_student(student_id: int):
    """Get single student record details."""
    student = student_service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student #{student_id} not found.")
    return student.to_dict()


@app.put("/api/students/{student_id}")
async def update_student(student_id: int, payload: StudentPayload):
    """Update student record with optimistic concurrency protection."""
    data = payload.model_dump()
    expected_updated_at = data.pop("expected_updated_at", None)

    success, updated, errors = student_service.update_student(
        student_id=student_id,
        data=data,
        expected_updated_at=expected_updated_at,
        current_user=web_admin_user,
    )
    if not success:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": errors},
        )
    return {"success": True, "student": updated.to_dict()}


@app.delete("/api/students/{student_id}")
async def delete_student(student_id: int, permanent: bool = False):
    """Soft delete (archive) or permanently remove student record."""
    ok, err = student_service.delete_student(
        student_id=student_id, permanent=permanent, current_user=web_admin_user
    )
    if not ok:
        raise HTTPException(status_code=400, detail=err or "Deletion failed.")
    return {"success": True, "message": "Record deleted successfully."}


@app.post("/api/students/{student_id}/restore")
async def restore_student(student_id: int):
    """Restore an archived student back to active status."""
    ok, err = student_service.restore_student(student_id=student_id, current_user=web_admin_user)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "Restoration failed.")
    return {"success": True, "message": "Record restored successfully."}


@app.get("/api/dashboard")
async def get_dashboard():
    """Return live dashboard metrics, counts, and breakdown tables."""
    return student_service.get_dashboard_stats()


@app.get("/api/audit")
async def get_audit_trail(limit: int = 150):
    """Return database audit trail entries."""
    return student_service.get_audit_logs(limit=limit)


@app.post("/api/backup")
async def create_backup():
    """Trigger an online database snapshot backup."""
    try:
        backup_path = student_service.create_database_backup()
        return {"success": True, "filename": backup_path.name, "path": str(backup_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database backup failed: {e}")


@app.get("/api/export/csv")
async def export_csv():
    """Export all student records to CSV."""
    students, _ = student_service.student_dao.search_students(
        limit=100000, offset=0, include_archived=True
    )
    temp_file = Path(tempfile.gettempdir()) / f"students_export_{len(students)}.csv"
    export_students_to_csv(students, temp_file)
    return FileResponse(
        temp_file,
        media_type="text/csv",
        filename=f"students_export_{len(students)}.csv",
    )


@app.get("/api/export/pdf")
async def export_pdf():
    """Export formatted institutional PDF report with ReportLab."""
    students, _ = student_service.student_dao.search_students(
        limit=100000, offset=0, include_archived=True
    )
    temp_file = Path(tempfile.gettempdir()) / f"students_report_{len(students)}.pdf"
    export_students_to_pdf(students, temp_file, title="Institutional Student Directory")
    return FileResponse(
        temp_file,
        media_type="application/pdf",
        filename=f"students_report_{len(students)}.pdf",
    )


@app.post("/api/import")
async def import_file(file: UploadFile = File(...)):
    """Upload and bulk import CSV or Excel students file."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Please upload a .csv, .xlsx, or .xls file.",
        )

    temp_path = Path(tempfile.gettempdir()) / f"import_upload_{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        ok, count, errors = import_students_from_file(
            temp_path,
            current_user=web_admin_user,
            student_dao=student_service.student_dao,
        )

        if not ok:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "errors": errors},
            )
        return {"success": True, "count": count}
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.web_server:app", host="127.0.0.1", port=8000, reload=False)
