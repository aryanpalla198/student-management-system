# Database Entity-Relationship (ER) Specification

## Conceptual Model

The database design provides a 3rd Normal Form (3NF) relational architecture ensuring ACID compliance, strict referential integrity, and query performance through index coverage.

```mermaid
erDiagram
    DEPARTMENTS ||--o{ STUDENTS : "offers studies to"
    USERS ||--o{ AUDIT_LOG : "triggers"
    
    DEPARTMENTS {
        INTEGER department_id PK "AUTOINCREMENT"
        VARCHAR name UK "NOT NULL, UNIQUE"
    }

    STUDENTS {
        INTEGER student_id PK "AUTOINCREMENT"
        VARCHAR roll_number UK "NOT NULL, UNIQUE, 5-20 chars"
        VARCHAR first_name "NOT NULL, 1-50 chars"
        VARCHAR last_name "NOT NULL, 1-50 chars"
        DATE date_of_birth "NOT NULL, Age 15-60"
        VARCHAR email UK "NOT NULL, UNIQUE, Valid email"
        VARCHAR phone "Optional, 7-15 digits"
        INTEGER department_id FK "NOT NULL -> departments.department_id"
        INTEGER year_level "NOT NULL, CHECK (1-6)"
        DECIMAL gpa "Optional, CHECK (0.00-10.00)"
        BOOLEAN is_archived "NOT NULL, DEFAULT 0"
        DATETIME created_at "NOT NULL, DEFAULT CURRENT_TIMESTAMP"
        DATETIME updated_at "NOT NULL, DEFAULT CURRENT_TIMESTAMP"
    }

    USERS {
        INTEGER user_id PK "AUTOINCREMENT"
        VARCHAR username UK "NOT NULL, UNIQUE"
        VARCHAR password_hash "NOT NULL, bcrypt"
        VARCHAR role "NOT NULL, CHECK ('ADMIN', 'STAFF')"
        BOOLEAN is_active "NOT NULL, DEFAULT 1"
    }

    AUDIT_LOG {
        INTEGER log_id PK "AUTOINCREMENT"
        INTEGER user_id FK "Optional -> users.user_id"
        VARCHAR action "NOT NULL, INSERT/UPDATE/ARCHIVE/DELETE"
        VARCHAR table_name "NOT NULL"
        INTEGER record_id "NOT NULL"
        TEXT details "Description of mutation"
        DATETIME changed_at "NOT NULL, DEFAULT CURRENT_TIMESTAMP"
    }
```

## Performance Indexes

The following targeted indexes ensure sub-millisecond retrieval on large datasets:

| Index Name | Target Table | Indexed Columns | Justification |
|---|---|---|---|
| `idx_students_name` | `students` | `(last_name, first_name)` | Accelerates name sorting and prefix searches |
| `idx_students_department` | `students` | `department_id` | Optimizes foreign key joins with departments |
| `idx_students_year` | `students` | `year_level` | Speeds up year-level cohort filtering |
| `idx_students_archived` | `students` | `is_archived` | Drastically optimizes filtering active vs archived records |
| `idx_audit_record` | `audit_log` | `(table_name, record_id)` | Enables instantaneous historical audit lookups |

## Data Integrity Guarantees

1. **Foreign Key Enforcement:** SQLite `PRAGMA foreign_keys = ON;` is enforced at the connection layer.
2. **Optimistic Locking:** The `updated_at` timestamp prevents concurrent edit collisions across multi-user environments.
3. **Atomic Operations:** All multi-step write processes (student creation, bulk import, archiving) are wrapped inside transactional blocks with automatic rollback on error.
