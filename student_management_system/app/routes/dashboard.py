from datetime import date, timedelta

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Attendance, Course, Department, Mark, Student

bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@login_required
def index():
    today = date.today()
    todays_records = db.session.scalar(
        db.select(func.count(Attendance.id)).where(Attendance.attendance_date == today)
    ) or 0
    todays_present = db.session.scalar(
        db.select(func.count(Attendance.id)).where(
            Attendance.attendance_date == today, Attendance.status == "present"
        )
    ) or 0
    attendance_percent = round(todays_present * 100 / todays_records, 1) if todays_records else 0

    enrollment = db.session.execute(
        db.select(Course.course_name, func.count(Student.id))
        .outerjoin(Student, Student.course_id == Course.id)
        .group_by(Course.id, Course.course_name)
        .order_by(Course.course_name)
    ).all()
    start_date = today - timedelta(days=6)
    attendance_rows = db.session.execute(
        db.select(Attendance.attendance_date, Attendance.status, func.count(Attendance.id))
        .where(Attendance.attendance_date >= start_date, Attendance.attendance_date <= today)
        .group_by(Attendance.attendance_date, Attendance.status)
        .order_by(Attendance.attendance_date)
    ).all()
    attendance_by_day = {start_date + timedelta(days=i): 0 for i in range(7)}
    for record_date, status, count in attendance_rows:
        attendance_by_day[record_date] += count if status == "present" else 0
    attendance_labels = [day.strftime("%b %d") for day in attendance_by_day]

    return render_template(
        "dashboard.html",
        total_students=db.session.scalar(db.select(func.count(Student.id))) or 0,
        active_students=db.session.scalar(
            db.select(func.count(Student.id)).where(Student.status == "active")
        ) or 0,
        total_courses=db.session.scalar(db.select(func.count(Course.id))) or 0,
        total_departments=db.session.scalar(db.select(func.count(Department.id))) or 0,
        attendance_percent=attendance_percent,
        exam_records=db.session.scalar(db.select(func.count(Mark.id))) or 0,
        enrollment_labels=[row[0] for row in enrollment],
        enrollment_values=[row[1] for row in enrollment],
        attendance_labels=attendance_labels,
        attendance_values=[attendance_by_day[day] for day in attendance_by_day],
        recent_students=db.session.scalars(
            db.select(Student)
            .options(joinedload(Student.course))
            .order_by(Student.admission_date.desc(), Student.id.desc())
            .limit(5)
        ).all(),
        recent_marks=db.session.scalars(
            db.select(Mark)
            .options(joinedload(Mark.student), joinedload(Mark.course))
            .order_by(Mark.created_at.desc())
            .limit(5)
        ).all(),
    )
