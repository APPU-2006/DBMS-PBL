"""Create the SMS relational schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "administrators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.UniqueConstraint("email", name="uq_administrators_email"),
    )
    op.create_index("ix_administrators_email", "administrators", ["email"], unique=False)

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("department_code", sa.String(length=20), nullable=False),
        sa.Column("department_name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.UniqueConstraint("department_code", name="uq_departments_department_code"),
        sa.UniqueConstraint("department_name", name="uq_departments_department_name"),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_code", sa.String(length=20), nullable=False),
        sa.Column("course_name", sa.String(length=150), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("duration_years", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.CheckConstraint("duration_years > 0", name="ck_courses_duration_positive"),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"],
            name="fk_courses_department_id_departments", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("course_code", name="uq_courses_course_code"),
    )
    op.create_index("ix_courses_department", "courses", ["department_id"], unique=False)

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.String(length=30), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("phone", sa.String(length=30)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("gender", sa.String(length=30)),
        sa.Column("address", sa.Text()),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("admission_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.CheckConstraint(
            "status IN ('active', 'graduated', 'discontinued')", name="ck_students_status"
        ),
        sa.ForeignKeyConstraint(
            ["course_id"], ["courses.id"],
            name="fk_students_course_id_courses", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("email", name="uq_students_email"),
        sa.UniqueConstraint("student_id", name="uq_students_student_id"),
    )
    op.create_index("ix_students_student_id", "students", ["student_id"], unique=False)
    op.create_index("ix_students_email", "students", ["email"], unique=False)
    op.create_index("ix_students_status", "students", ["status"], unique=False)
    op.create_index(
        "ix_students_course_status", "students", ["course_id", "status"], unique=False
    )

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("remarks", sa.String(length=255)),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.CheckConstraint(
            "status IN ('present', 'absent', 'late')", name="ck_attendance_status"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"],
            name="fk_attendance_student_id_students", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "student_id", "attendance_date", name="uq_attendance_student_day"
        ),
    )
    op.create_index(
        "ix_attendance_attendance_date", "attendance", ["attendance_date"], unique=False
    )
    op.create_index(
        "ix_attendance_date_status", "attendance", ["attendance_date", "status"], unique=False
    )

    op.create_table(
        "marks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("subject_name", sa.String(length=120), nullable=False),
        sa.Column("exam_type", sa.String(length=60), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("maximum_marks", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.CheckConstraint("maximum_marks > 0", name="ck_marks_maximum_positive"),
        sa.CheckConstraint(
            "marks_obtained >= 0 AND marks_obtained <= maximum_marks",
            name="ck_marks_in_range",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"], ["courses.id"],
            name="fk_marks_course_id_courses", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"],
            name="fk_marks_student_id_students", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "student_id", "subject_name", "exam_type", name="uq_marks_student_subject_exam"
        ),
    )
    op.create_index("ix_marks_course_exam_date", "marks", ["course_id", "exam_date"], unique=False)


def downgrade():
    op.drop_index("ix_marks_course_exam_date", table_name="marks")
    op.drop_table("marks")
    op.drop_index("ix_attendance_date_status", table_name="attendance")
    op.drop_index("ix_attendance_attendance_date", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index("ix_students_course_status", table_name="students")
    op.drop_index("ix_students_status", table_name="students")
    op.drop_index("ix_students_email", table_name="students")
    op.drop_index("ix_students_student_id", table_name="students")
    op.drop_table("students")
    op.drop_index("ix_courses_department", table_name="courses")
    op.drop_table("courses")
    op.drop_table("departments")
    op.drop_index("ix_administrators_email", table_name="administrators")
    op.drop_table("administrators")
