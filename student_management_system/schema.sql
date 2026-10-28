CREATE DATABASE IF NOT EXISTS student_management_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE student_management_db;

CREATE TABLE IF NOT EXISTS administrators (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'admin',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  department_code VARCHAR(20) NOT NULL UNIQUE,
  department_name VARCHAR(120) NOT NULL UNIQUE,
  description TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_code VARCHAR(20) NOT NULL UNIQUE,
  course_name VARCHAR(150) NOT NULL,
  department_id INT NOT NULL,
  duration_years INT NOT NULL,
  description TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT ck_courses_duration_positive CHECK (duration_years > 0),
  CONSTRAINT fk_courses_department FOREIGN KEY (department_id)
    REFERENCES departments(id) ON DELETE RESTRICT,
  INDEX ix_courses_department (department_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(30) NOT NULL UNIQUE,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  phone VARCHAR(30),
  date_of_birth DATE,
  gender VARCHAR(30),
  address TEXT,
  course_id INT NOT NULL,
  admission_date DATE NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT ck_students_status CHECK (status IN ('active', 'graduated', 'discontinued')),
  CONSTRAINT fk_students_course FOREIGN KEY (course_id)
    REFERENCES courses(id) ON DELETE RESTRICT,
  INDEX ix_students_course_status (course_id, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  attendance_date DATE NOT NULL,
  status VARCHAR(10) NOT NULL,
  remarks VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_attendance_student_day UNIQUE (student_id, attendance_date),
  CONSTRAINT ck_attendance_status CHECK (status IN ('present', 'absent', 'late')),
  CONSTRAINT fk_attendance_student FOREIGN KEY (student_id)
    REFERENCES students(id) ON DELETE RESTRICT,
  INDEX ix_attendance_date_status (attendance_date, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS marks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  subject_name VARCHAR(120) NOT NULL,
  exam_type VARCHAR(60) NOT NULL,
  marks_obtained DECIMAL(7,2) NOT NULL,
  maximum_marks DECIMAL(7,2) NOT NULL,
  exam_date DATE NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_marks_student_subject_exam UNIQUE (student_id, subject_name, exam_type),
  CONSTRAINT ck_marks_maximum_positive CHECK (maximum_marks > 0),
  CONSTRAINT ck_marks_in_range CHECK (marks_obtained >= 0 AND marks_obtained <= maximum_marks),
  CONSTRAINT fk_marks_student FOREIGN KEY (student_id)
    REFERENCES students(id) ON DELETE RESTRICT,
  CONSTRAINT fk_marks_course FOREIGN KEY (course_id)
    REFERENCES courses(id) ON DELETE RESTRICT,
  INDEX ix_marks_course_exam_date (course_id, exam_date)
) ENGINE=InnoDB;
