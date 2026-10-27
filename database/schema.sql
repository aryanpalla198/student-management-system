-- =====================================================================
-- Student Management System: Database Schema
-- Compatible with SQLite 3 and portable to MySQL / PostgreSQL
-- =====================================================================

PRAGMA foreign_keys = ON;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number     VARCHAR(20)  NOT NULL UNIQUE,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    date_of_birth   DATE         NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone           VARCHAR(15),
    department_id   INTEGER      NOT NULL,
    year_level      INTEGER      NOT NULL CHECK (year_level BETWEEN 1 AND 6),
    gpa             DECIMAL(3,2) CHECK (gpa IS NULL OR (gpa >= 0.00 AND gpa <= 10.00)),
    is_archived     BOOLEAN      NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at      DATETIME     NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 3. Users Table (for Authentication & Role-Based Access Control)
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(10)  NOT NULL CHECK (role IN ('ADMIN', 'STAFF')),
    is_active       BOOLEAN      NOT NULL DEFAULT 1
);

-- 4. Audit Log Table (Tracking all data modifications)
CREATE TABLE IF NOT EXISTS audit_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    action          VARCHAR(20)  NOT NULL,   -- INSERT / UPDATE / ARCHIVE / DELETE / RESTORE
    table_name      VARCHAR(50)  NOT NULL,
    record_id       INTEGER      NOT NULL,
    details         TEXT,
    changed_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Indexes for performance and query optimization
CREATE INDEX IF NOT EXISTS idx_students_name       ON students(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_students_department ON students(department_id);
CREATE INDEX IF NOT EXISTS idx_students_year       ON students(year_level);
CREATE INDEX IF NOT EXISTS idx_students_archived   ON students(is_archived);
CREATE INDEX IF NOT EXISTS idx_audit_record        ON audit_log(table_name, record_id);
