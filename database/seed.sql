-- =====================================================================
-- Student Management System: Seed Data
-- =====================================================================

-- Insert Departments
INSERT OR IGNORE INTO departments (department_id, name) VALUES
(1, 'Computer Science & Engineering'),
(2, 'Electronics & Communication'),
(3, 'Mechanical Engineering'),
(4, 'Information Technology'),
(5, 'Business Administration'),
(6, 'Mathematics & Computing');

-- Insert Initial Users (Passwords: Admin@123 and Staff@123 hashed with bcrypt)
INSERT OR IGNORE INTO users (user_id, username, password_hash, role, is_active) VALUES
(1, 'admin', '$2b$12$ud6vM.nYofPOnWOb2XtA7eg94.Sg1/Yx/ws7gk44CNzNu9rY5dyQi', 'ADMIN', 1),
(2, 'staff', '$2b$12$MhkZo0RVPkgJ.dt.kd.igOLU00Q8pD8GfEH65/MQVEiFuxaqKgOcq', 'STAFF', 1);

-- Insert Sample Students
INSERT OR IGNORE INTO students (
    student_id, roll_number, first_name, last_name, date_of_birth,
    email, phone, department_id, year_level, gpa, is_archived, created_at, updated_at
) VALUES
(1, 'CS2023001', 'Alice', 'Smith', '2004-05-14', 'alice.smith@university.edu', '+15550101', 1, 3, 9.45, 0, '2023-08-15 09:00:00', '2023-08-15 09:00:00'),
(2, 'CS2023002', 'Bob', 'Johnson', '2003-11-20', 'bob.johnson@university.edu', '+15550102', 1, 3, 8.70, 0, '2023-08-15 09:10:00', '2023-08-15 09:10:00'),
(3, 'EC2024001', 'Charlie', 'Brown', '2005-02-18', 'charlie.brown@university.edu', '+15550103', 2, 2, 8.15, 0, '2024-08-12 10:00:00', '2024-08-12 10:00:00'),
(4, 'ME2022001', 'Diana', 'Prince', '2002-09-08', 'diana.prince@university.edu', '+15550104', 3, 4, 9.80, 0, '2022-08-10 11:30:00', '2022-08-10 11:30:00'),
(5, 'IT2023001', 'Ethan', 'Hunt', '2004-07-25', 'ethan.hunt@university.edu', '+15550105', 4, 3, 7.90, 0, '2023-08-16 14:00:00', '2023-08-16 14:00:00'),
(6, 'BA2025001', 'Fiona', 'Gallagher', '2006-03-30', 'fiona.g@university.edu', '+15550106', 5, 1, 8.60, 0, '2025-08-18 09:20:00', '2025-08-18 09:20:00'),
(7, 'MC2024001', 'George', 'Clark', '2005-12-12', 'george.clark@university.edu', '+15550107', 6, 2, 9.10, 0, '2024-08-14 11:00:00', '2024-08-14 11:00:00'),
(8, 'CS2025001', 'Hannah', 'Abbott', '2006-08-05', 'hannah.a@university.edu', '+15550108', 1, 1, 8.25, 0, '2025-08-20 10:15:00', '2025-08-20 10:15:00'),
(9, 'EC2022001', 'Ian', 'Malcolm', '2002-04-16', 'ian.malcolm@university.edu', '+15550109', 2, 4, 7.40, 0, '2022-08-11 15:45:00', '2022-08-11 15:45:00'),
(10, 'ME2023001', 'Julia', 'Roberts', '2004-01-22', 'julia.roberts@university.edu', '+15550110', 3, 3, 8.95, 0, '2023-08-17 12:00:00', '2023-08-17 12:00:00'),
(11, 'BA2024001', 'Kevin', 'Bacon', '2005-06-19', 'kevin.bacon@university.edu', '+15550111', 5, 2, 7.85, 0, '2024-08-15 13:20:00', '2024-08-15 13:20:00'),
(12, 'CS2022001', 'Laura', 'Croft', '2002-10-10', 'laura.croft@university.edu', '+15550112', 1, 4, 9.60, 0, '2022-08-09 09:30:00', '2022-08-09 09:30:00'),
(13, 'IT2025001', 'Michael', 'Scott', '2006-03-15', 'michael.scott@university.edu', '+15550113', 4, 1, 6.75, 0, '2025-08-21 16:00:00', '2025-08-21 16:00:00'),
(14, 'MC2023001', 'Nancy', 'Drew', '2004-09-02', 'nancy.drew@university.edu', '+15550114', 6, 3, 9.30, 0, '2023-08-18 10:45:00', '2023-08-18 10:45:00'),
(15, 'CS2021001', 'Oliver', 'Queen', '2001-05-16', 'oliver.queen@university.edu', '+15550115', 1, 4, 8.40, 1, '2021-08-10 10:00:00', '2024-06-15 11:00:00');

-- Record initial audit log for seeding
INSERT OR IGNORE INTO audit_log (log_id, user_id, action, table_name, record_id, details, changed_at) VALUES
(1, 1, 'SEED', 'students', 0, 'Initial database seed population with 15 records', CURRENT_TIMESTAMP);
