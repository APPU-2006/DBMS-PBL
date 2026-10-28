# Student Management System (SMS)

A database-backed academic administration application for a BCA DBMS project. It uses Flask and SQLAlchemy with **MySQL 8 as the application database**. The app does not silently fall back to SQLite. SQLite is used only by the isolated automated test suite.

## Objectives and features

- Session-based administrator sign-in, password hashing, CSRF protection and safe post-login redirects.
- Dashboard statistics, recent activity and database-backed enrollment and attendance charts.
- Student records with search, filters, pagination, sorting, profile details and guarded deletion.
- Department and course management with database foreign keys and safe deletion checks.
- Bulk course attendance with duplicate-safe updates and attendance summaries.
- Examination marks, validation, percentages and demonstration grades.
- Filterable academic reports, print layout and formula-safe CSV export.
- MySQL schema, repeatable demo seeding, migrations and automated tests.

## Technology and requirements

- Python 3.11 or newer (3.11 is recommended for the course project).
- MySQL Server 8.x and MySQL command-line client (or MySQL Workbench).
- Visual Studio Code with the Python extension.
- Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate, PyMySQL and pytest.
- A modern browser. Bootstrap, icons and Chart.js are loaded from jsDelivr.

## Folder structure

```text
student_management_system/
├── app/
│   ├── routes/                 # Blueprints for each feature
│   ├── templates/              # Jinja pages and error states
│   ├── static/                 # CSS and JavaScript
│   ├── extensions.py
│   ├── forms.py
│   └── models.py
├── migrations/                 # Initial Alembic migration and environment
├── scripts/                    # Explicit schema initialization and sample data
├── tests/                      # Isolated SQLite tests
├── .env.example
├── config.py
├── requirements.txt
├── run.py
└── schema.sql
```

## Database design and relationships

The database is named `student_management_db` and contains:

| Table | Purpose and key relationship |
|---|---|
| `administrators` | Administrator accounts; stores Werkzeug password hashes only. |
| `departments` | Unique department code and name; one department has many courses. |
| `courses` | Belongs to a department; one course has many enrolled students and marks. |
| `students` | Belongs to one course; has multiple attendance rows and examination marks. |
| `attendance` | Belongs to one student; unique per student and date. |
| `marks` | Links one student with one course and an exam subject/type. A student/subject/exam-type combination is unique. |

Foreign keys use `ON DELETE RESTRICT` for academic records. Students and courses with dependent records cannot be deleted. Archive a student by changing their status instead. Attendance percentage is **present records / all attendance records in the reporting period × 100**. Late records count in the denominator but not the numerator. A student with no attendance has 0%, not a divide-by-zero error.

Marks are constrained to 0 through the record's own `maximum_marks`, which must be positive. The demonstration grading thresholds (A+ ≥ 90, A ≥ 80, B+ ≥ 70, B ≥ 60, C ≥ 50, D ≥ 40, otherwise F) are illustrative only, not an official GM University policy.

### Set up MySQL

1. Start the MySQL 8 service.
2. In MySQL Workbench or a MySQL command prompt, create a local database/user (recommended for the migration-based setup). Example:

   ```sql
   CREATE DATABASE student_management_db
     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'sms_user'@'localhost' IDENTIFIED BY 'choose-a-local-password';
   GRANT ALL PRIVILEGES ON student_management_db.* TO 'sms_user'@'localhost';
   ```

   Alternatively, `schema.sql` creates the database and all six tables. If you choose this complete SQL setup, do not run the initial migration upgrade afterward. Run the schema script from PowerShell if the MySQL client is on PATH:

   ```powershell
   mysql -u root -p < schema.sql
   ```

3. Use your MySQL username/password in `.env`. URL-encode special characters in `DATABASE_URL` (for example `@` as `%40`); the alternative `MYSQL_USER` / `MYSQL_PASSWORD` settings are URL-encoded by the app.

## Install and configure in Windows / VS Code

Open the `student_management_system` folder in VS Code. In the integrated PowerShell terminal:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or run the virtual environment directly with `.\.venv\Scripts\python.exe`.

Edit `.env` and set a long random `SECRET_KEY` and the connection string, for example:

```dotenv
SECRET_KEY=replace-with-a-random-secret
DATABASE_URL=mysql+pymysql://sms_user:your_password@localhost:3306/student_management_db?charset=utf8mb4
DEMO_ADMIN_EMAIL=admin@sms.local
DEMO_ADMIN_PASSWORD=Admin@12345
SESSION_COOKIE_SECURE=0
```

Do not commit `.env`. Its example defaults are for local coursework, not for deployment. On an HTTPS production deployment, set `SESSION_COOKIE_SECURE=1`, use a secret unique to the deployment, and change or disable the displayed demo credentials. The secure cookie setting is off in local HTTP development so the browser can send the session cookie.

## Initialize, seed and run

For the recommended setup above (database exists, tables do not), use the checked-in Alembic migration to create the schema:

```powershell
flask --app run.py db upgrade
python -m scripts.seed_demo_data
python run.py
```

`db upgrade` applies committed schema migrations and preserves existing records. For a simple one-time setup without Alembic, `python -m scripts.init_db` verifies MySQL and creates any missing ORM tables; it does not drop tables. Do not use both setup approaches on a pre-existing, manually-created schema unless it has been checked first.

If you created all tables with `schema.sql`, run `flask --app run.py db stamp head` once before seeding so Alembic recognizes that the initial schema is already present. Do not use `db upgrade` on those already-created tables.

Then visit <http://127.0.0.1:5000>. Demo sign-in:

- Email: `admin@sms.local`
- Password: `Admin@12345`

The seed script creates an admin if absent plus sample departments, courses, 10 fictional students, attendance and marks. It is safe to rerun: matching records are kept and missing demo records are added. It never resets tables.

For future schema edits, update the SQLAlchemy model, then run:

```powershell
flask --app run.py db migrate -m "Describe the schema change"
flask --app run.py db upgrade
```

Review generated migrations before applying them to important data. Never use `drop_all` against a development or production MySQL database.

## Tests

With the virtual environment activated:

```powershell
python -m scripts.run_tests
```

Tests create an isolated in-memory SQLite database per test fixture; they do not connect to, initialize, or delete data from MySQL. They cover authentication, protected routes, CRUD, constraints, marks and attendance calculations. MySQL-specific connectivity and migration behavior still require a configured local MySQL service.

The runner also handles a Python environment that has a standalone `py.py` module shadowing pytest's optional legacy `py.path` compatibility module. In a standard Python installation, `pytest` runs the same suite directly.

## Common setup problems

- **Can't connect to MySQL:** start the MySQL service and confirm host, port, user privileges and database name in `.env`.
- **Access denied:** verify the account/password and grant access to `student_management_db`.
- **Special characters in a URL password:** percent-encode them or use `MYSQL_USER` and `MYSQL_PASSWORD` environment variables instead.
- **`flask` command not found:** activate `.venv` and reinstall `requirements.txt`; the command is also available as `python -m flask`.
- **PowerShell refuses activation:** use the execution-policy command above or invoke `.venv\Scripts\python.exe` directly.
- **Login cookie does not persist on localhost:** keep `SESSION_COOKIE_SECURE=0` for HTTP local use; only enable secure cookies behind HTTPS.
- **Demo password is not accepted:** ensure the seed script ran against the same `DATABASE_URL` used by the app.

## DBMS demonstration queries (MySQL)

These are illustrative SQL statements for academic demonstration. Normal application reads/writes use SQLAlchemy ORM, and the Flask application does not execute this section automatically.

```sql
-- CREATE DATABASE
CREATE DATABASE student_management_db CHARACTER SET utf8mb4;

-- A small CREATE TABLE example (the full definitions are in schema.sql)
CREATE TABLE example_subject (
  id INT PRIMARY KEY AUTO_INCREMENT,
  subject_name VARCHAR(120) NOT NULL UNIQUE
);

-- INSERT and SELECT
INSERT INTO departments (department_code, department_name)
VALUES ('BIO', 'Biology');
SELECT department_code, department_name FROM departments;

-- WHERE and ORDER BY
SELECT student_id, first_name, last_name
FROM students
WHERE status = 'active'
ORDER BY last_name, first_name;

-- INNER JOIN: student, course and department
SELECT s.student_id, s.first_name, s.last_name, c.course_name, d.department_name
FROM students AS s
INNER JOIN courses AS c ON c.id = s.course_id
INNER JOIN departments AS d ON d.id = c.department_id;

-- LEFT JOIN: include courses even when no students are enrolled
SELECT c.course_code, c.course_name, COUNT(s.id) AS student_count
FROM courses AS c
LEFT JOIN students AS s ON s.course_id = c.id
GROUP BY c.id, c.course_code, c.course_name;

-- GROUP BY and HAVING: courses with at least two active students
SELECT c.course_name, COUNT(s.id) AS active_count
FROM courses AS c
JOIN students AS s ON s.course_id = c.id
WHERE s.status = 'active'
GROUP BY c.id, c.course_name
HAVING COUNT(s.id) >= 2;

-- Department-wise counts
SELECT d.department_name, COUNT(s.id) AS student_count
FROM departments AS d
LEFT JOIN courses AS c ON c.department_id = d.id
LEFT JOIN students AS s ON s.course_id = c.id
GROUP BY d.id, d.department_name
ORDER BY student_count DESC;

-- Aggregate attendance: late counts in the total denominator, not as present
SELECT s.student_id,
       100.0 * SUM(a.status = 'present') / NULLIF(COUNT(a.id), 0) AS attendance_percent
FROM students AS s
LEFT JOIN attendance AS a ON a.student_id = s.id
GROUP BY s.id, s.student_id;

-- Student result percentages use each marks row's maximum_marks
SELECT s.student_id, m.subject_name, m.exam_type,
       m.marks_obtained, m.maximum_marks,
       100.0 * m.marks_obtained / m.maximum_marks AS percentage
FROM marks AS m
JOIN students AS s ON s.id = m.student_id
ORDER BY s.student_id, m.exam_date;

-- Aggregate average (course performance)
SELECT c.course_name, AVG(100.0 * m.marks_obtained / m.maximum_marks) AS average_percentage
FROM courses AS c
JOIN marks AS m ON m.course_id = c.id
GROUP BY c.id, c.course_name;

-- UPDATE
UPDATE students SET status = 'graduated' WHERE student_id = 'SMS2026001';

-- DELETE example; dependent records are protected by RESTRICT foreign keys
DELETE FROM departments WHERE department_code = 'BIO';

-- Primary key, foreign key and UNIQUE constraints are declared in schema.sql.
-- Transaction demonstration (commit only if both statements succeed)
START TRANSACTION;
INSERT INTO departments (department_code, department_name)
VALUES ('ART', 'Arts');
UPDATE courses SET department_id = LAST_INSERT_ID() WHERE course_code = 'ART1';
COMMIT;
```

## Future enhancements

Role-based staff accounts, student self-service portal, configurable academic terms and grading policies, audit history, scheduled backups, and exportable PDF reports.
