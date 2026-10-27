# 🎓 AcademiaSMS: Enterprise Student Management System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-2563EB?style=for-the-badge&logo=googlechrome&logoColor=white)](https://aryanpalla198.github.io/student-management-system/)
[![Tests](https://img.shields.io/badge/Tests-45%20Passed%20(92%25%20Coverage)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/aryanpalla198/student-management-system)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/aryanpalla198/student-management-system)

> 🌐 **Live Web Application in Chrome:** **[https://aryanpalla198.github.io/student-management-system/](https://aryanpalla198.github.io/student-management-system/)**

A high-performance enterprise application designed for institutional academic administration. Available as both a **Desktop Application** (Tkinter/ttk + SQLite WAL) and a **Live Web Application** (Chrome / GitHub Pages).

---

## 📸 Key Highlights & Features

- **🎨 Premium, Neat Color Themes:** Crafted with a modern color palette supporting instantaneous **Light Mode** (Crisp Slate/Royal Blue) and **Dark Mode** (Deep Obsidian/Electric Blue).
- **🛡️ 3-Tier Layered Architecture:** Complete decoupling between the Presentation layer (Tkinter GUI), Business/Service layer (validation, authorization, rate limiting), and Data Access Object layer (parameterized SQL, transactions).
- **🔐 Security & Authentication:** Passwords hashed with `bcrypt` (12 rounds of salt). Brute-force protection automatically locks accounts for 60 seconds after 3 failed login attempts.
- **⚡ High-Performance Querying:** Paginated search (`LIMIT` / `OFFSET`), debounced search bar (300ms), and composite indexes across `(last_name, first_name)`, `department_id`, `year_level`, and `is_archived`.
- **🔄 Concurrency Protection:** Optimistic locking via high-precision `updated_at` timestamps prevents concurrent edit collisions across multi-user sessions.
- **📦 Data Integrity & Auditing:** Database-level `CHECK`, `UNIQUE`, `NOT NULL`, and `FOREIGN KEY` constraints enforced via SQLite WAL mode, plus a comprehensive `audit_log` tracking all mutations.
- **📁 Multi-Format Import/Export:** Atomic bulk import from CSV and Excel (`pandas` / `openpyxl`) with all-or-nothing rollback on validation errors, plus CSV and PDF report generation (`reportlab`).
- **💾 Hot Online Backups:** Instantaneous non-blocking database backup snapshots using SQLite's online backup engine.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│               Presentation Layer (GUI)                 │
│  Tkinter / ttk Windows, Debounced Search, Stat Cards   │
├────────────────────────────────────────────────────────┤
│             Service / Business Logic Layer             │
│  Field Validators, Role Permissions, Concurrency Lock  │
├────────────────────────────────────────────────────────┤
│             Data Access Object (DAO) Layer             │
│  Parameterized SQL Queries, Transactions, Audit Trail   │
├────────────────────────────────────────────────────────┤
│                 Database Engine (SQL)                  │
│  SQLite 3 (WAL Mode, Foreign Keys, Composite Indexes)  │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
student_management_system/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Application entry point & lifecycle manager
│   ├── config.py                # Database paths, constants & color palettes
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── login_window.py      # Authentication dialog with countdown lockout
│   │   ├── main_window.py       # Main dashboard, students registry & navigation
│   │   ├── student_form.py      # Add/Edit student modal with validation
│   │   ├── dashboard_view.py    # Metric stat cards & department breakdown
│   │   └── widgets.py           # High-DPI scaling, themes, search bar & pagination
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # bcrypt authentication, rate limiting & session
│   │   └── student_service.py   # Business logic, optimistic locking & RBAC
│   ├── dao/
│   │   ├── __init__.py
│   │   ├── db_connection.py     # Connection manager & SQLite backup engine
│   │   ├── student_dao.py       # Student CRUD, search, pagination & audit log
│   │   └── user_dao.py          # User lookups and credentials management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── student.py           # Student & Department domain dataclasses
│   │   └── user.py              # User domain dataclass
│   └── utils/
│       ├── __init__.py
│       ├── validators.py        # Business validation rules (roll, email, age 15-60)
│       ├── importer.py          # CSV/Excel atomic import, CSV/PDF report generator
│       └── logger.py            # Structured logging to file and console
├── database/
│   ├── schema.sql               # DDL with tables, constraints and indexes
│   ├── seed.sql                 # Sample departments, users, and students
│   └── migrations/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Isolated temporary SQLite database fixtures
│   ├── test_validators.py       # Unit tests for validation functions
│   ├── test_user_dao.py         # Integration tests for UserDAO
│   ├── test_student_dao.py      # Integration tests for StudentDAO (CRUD, constraints)
│   ├── test_student_service.py  # Unit tests for business rules & permissions
│   ├── test_auth_service.py     # Unit tests for bcrypt and login rate limiting
│   └── test_importer.py         # Unit tests for CSV/Excel import & PDF export
├── docs/
│   ├── ER_diagram.md            # Entity-Relationship diagram & indexing specs
│   └── user_manual.md           # End-user and staff operational manual
├── backups/                     # Auto-generated database backup directory
├── logs/                        # System runtime logs (app.log)
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ installed (`py` or `python` command)

### 2. Installation
Clone or navigate to the project directory:
```bash
cd C:\Users\aryan\.gemini\antigravity\scratch\student_management_system
```

Install required dependencies:
```bash
py -m pip install -r requirements.txt
```

### 3. Running the Application
Launch the desktop application:
```bash
py app/main.py
```
*Note: On initial launch, the system automatically initializes the database schema and seeds sample departments, users, and student records.*

---

## 🔑 Default Credentials

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `Admin@123` | **ADMIN** | Full CRUD, Permanent Hard Delete, System Backup, Full Audit Access |
| `staff` | `Staff@123` | **STAFF** | Student Search, Create, Edit, and Soft Delete (Archive) |

---

## 🧪 Running the Test Suite

Run all 45 automated unit and integration tests:
```bash
py -m pytest tests -v
```

Generate a test coverage report for the core services and DAO layers:
```bash
py -m pytest --cov=app.services --cov=app.dao --cov=app.utils --cov=app.models --cov-report=term-missing tests
```

### Coverage Summary:
- **`app/dao/db_connection.py`**: **98%**
- **`app/utils/validators.py`**: **96%**
- **`app/models/student.py`**: **94%**
- **`app/dao/student_dao.py`**: **93%**
- **`app/dao/user_dao.py`**: **100%**
- **`app/services/student_service.py`**: **88%**
- **`app/services/auth_service.py`**: **86%**
- **`app/utils/importer.py`**: **87%**
- **Overall Backend Layer Coverage**: **92%** (45 / 45 tests passing)

---

## 📊 Database Design & Indexes

### Tables
1. `departments` (`department_id` PK, `name` UNIQUE)
2. `students` (`student_id` PK, `roll_number` UNIQUE, `email` UNIQUE, `year_level` CHECK (1-6), `gpa` CHECK (0-10), `is_archived` DEFAULT 0)
3. `users` (`user_id` PK, `username` UNIQUE, `password_hash`, `role` CHECK ('ADMIN', 'STAFF'))
4. `audit_log` (`log_id` PK, `user_id` FK, `action`, `table_name`, `record_id`, `changed_at`)

### Index Coverage
- `idx_students_name`: `(last_name, first_name)`
- `idx_students_department`: `(department_id)`
- `idx_students_year`: `(year_level)`
- `idx_students_archived`: `(is_archived)`
- `idx_audit_record`: `(table_name, record_id)`
