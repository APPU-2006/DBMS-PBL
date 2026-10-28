import csv
import io

from flask import Blueprint, Response, render_template, request
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Attendance, Course, Department, Mark, Student

bp = Blueprint("reports", __name__)


def _student_query():
    query = db.select(Student).join(Course).join(Department)
    course_id = request.args.get("course_id", type=int)
    department_id = request.args.get("department_id", type=int)
    if course_id:
        query = query.where(Student.course_id == course_id)
    if department_id:
        query = query.where(Course.department_id == department_id)
    return query.order_by(Department.department_name, Course.course_name, Student.last_name)


def _safe_csv(value):
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


@bp.get("/")
@login_required
def index():
    students = db.session.scalars(_student_query()).all()
    course_id = request.args.get("course_id", type=int)
    department_id = request.args.get("department_id", type=int)
    attendance_query = (
        db.select(Attendance)
        .join(Student)
        .join(Course)
        .options(joinedload(Attendance.student).joinedload(Student.course))
    )
    marks_query = (
        db.select(Mark)
        .join(Student)
        .join(Course)
        .options(joinedload(Mark.student), joinedload(Mark.course))
    )
    performance_query = (
        db.select(Course.course_name, func.avg(Mark.marks_obtained * 100 / Mark.maximum_marks))
        .join(Mark, Mark.course_id == Course.id)
        .join(Department, Department.id == Course.department_id)
        .group_by(Course.id, Course.course_name)
        .order_by(Course.course_name)
    )
    if course_id:
        attendance_query = attendance_query.where(Student.course_id == course_id)
        marks_query = marks_query.where(Student.course_id == course_id)
    if department_id:
        attendance_query = attendance_query.where(Course.department_id == department_id)
        marks_query = marks_query.where(Course.department_id == department_id)
    if course_id:
        performance_query = performance_query.where(Course.id == course_id)
    if department_id:
        performance_query = performance_query.where(Department.id == department_id)
    attendance = db.session.scalars(
        attendance_query.order_by(Attendance.attendance_date.desc())
    ).all()
    marks = db.session.scalars(marks_query.order_by(Mark.exam_date.desc())).all()
    course_performance = db.session.execute(performance_query).all()
    admissions_by_year = {}
    for student in students:
        year = student.admission_date.year
        admissions_by_year[year] = admissions_by_year.get(year, 0) + 1
    return render_template(
        "reports/index.html",
        students=students,
        attendance=attendance,
        marks=marks,
        course_performance=course_performance,
        admissions=sorted(admissions_by_year.items(), reverse=True),
        courses=db.session.scalars(db.select(Course).order_by(Course.course_name)).all(),
        departments=db.session.scalars(db.select(Department).order_by(Department.department_name)).all(),
    )


@bp.get("/students.csv")
@login_required
def export_students():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        ["Student ID", "Name", "Email", "Course", "Department", "Admission date", "Status"]
    )
    for student in db.session.scalars(_student_query()).all():
        writer.writerow(
            [
                _safe_csv(student.student_id),
                _safe_csv(student.full_name),
                _safe_csv(student.email),
                _safe_csv(student.course.course_name),
                _safe_csv(student.course.department.department_name),
                student.admission_date.isoformat(),
                student.status,
            ]
        )
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=student-report.csv"},
    )
