from datetime import datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Administrator(UserMixin, db.Model):
    __tablename__ = "administrators"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="admin", server_default="admin")
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))
    created_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=db.func.now(),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Administrator {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(Administrator, int(user_id))
    except (TypeError, ValueError):
        return None


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    department_code = db.Column(db.String(20), unique=True, nullable=False)
    department_name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, server_default=db.func.now()
    )
    courses = db.relationship("Course", back_populates="department", lazy="select")


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    duration_years = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, server_default=db.func.now()
    )
    department = db.relationship("Department", back_populates="courses")
    students = db.relationship("Student", back_populates="course", lazy="select")
    marks = db.relationship("Mark", back_populates="course", lazy="select")
    __table_args__ = (
        CheckConstraint("duration_years > 0", name="ck_courses_duration_positive"),
        Index("ix_courses_department", "department_id"),
    )


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(30))
    address = db.Column(db.Text)
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    admission_date = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="active", server_default="active", index=True
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=db.func.now(),
    )
    course = db.relationship("Course", back_populates="students")
    attendance_records = db.relationship("Attendance", back_populates="student")
    marks = db.relationship("Mark", back_populates="student")
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'graduated', 'discontinued')",
            name="ck_students_status",
        ),
        Index("ix_students_course_status", "course_id", "status"),
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False)
    remarks = db.Column(db.String(255))
    created_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, server_default=db.func.now()
    )
    student = db.relationship("Student", back_populates="attendance_records")
    __table_args__ = (
        UniqueConstraint("student_id", "attendance_date", name="uq_attendance_student_day"),
        CheckConstraint(
            "status IN ('present', 'absent', 'late')", name="ck_attendance_status"
        ),
        Index("ix_attendance_date_status", "attendance_date", "status"),
    )


class Mark(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    subject_name = db.Column(db.String(120), nullable=False)
    exam_type = db.Column(db.String(60), nullable=False)
    marks_obtained = db.Column(db.Numeric(7, 2), nullable=False)
    maximum_marks = db.Column(db.Numeric(7, 2), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, server_default=db.func.now()
    )
    student = db.relationship("Student", back_populates="marks")
    course = db.relationship("Course", back_populates="marks")
    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_name", "exam_type", name="uq_marks_student_subject_exam"
        ),
        CheckConstraint("maximum_marks > 0", name="ck_marks_maximum_positive"),
        CheckConstraint(
            "marks_obtained >= 0 AND marks_obtained <= maximum_marks",
            name="ck_marks_in_range",
        ),
        Index("ix_marks_course_exam_date", "course_id", "exam_date"),
    )

    @property
    def percentage(self):
        if not self.maximum_marks:
            return Decimal("0")
        return self.marks_obtained * Decimal("100") / self.maximum_marks

    @property
    def grade(self):
        percentage = self.percentage
        if percentage >= 90:
            return "A+"
        if percentage >= 80:
            return "A"
        if percentage >= 70:
            return "B+"
        if percentage >= 60:
            return "B"
        if percentage >= 50:
            return "C"
        if percentage >= 40:
            return "D"
        return "F"
