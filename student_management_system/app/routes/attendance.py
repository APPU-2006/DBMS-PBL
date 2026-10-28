from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Attendance, Course, Student

bp = Blueprint("attendance", __name__)
VALID_STATUSES = {"present", "absent", "late"}


def _read_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@bp.route("/", methods=["GET", "POST"])
@login_required
def manage_attendance():
    courses = db.session.scalars(db.select(Course).order_by(Course.course_name)).all()
    course_id = request.values.get("course_id", type=int)
    attendance_date = _read_date(request.values.get("attendance_date"))
    if request.method == "POST":
        course = db.session.get(Course, course_id) if course_id else None
        if not course or not attendance_date:
            flash("Select a valid course and attendance date.", "danger")
            return redirect(url_for("attendance.manage_attendance"))
        students = db.session.scalars(
            db.select(Student).where(
                Student.course_id == course.id, Student.status == "active"
            ).order_by(Student.last_name, Student.first_name)
        ).all()
        submitted = {
            str(student.id): request.form.get(f"status_{student.id}") for student in students
        }
        if any(value not in VALID_STATUSES for value in submitted.values()):
            flash("Choose a valid attendance status for every listed student.", "danger")
            return redirect(
                url_for(
                    "attendance.manage_attendance",
                    course_id=course.id,
                    attendance_date=attendance_date.isoformat(),
                )
            )
        existing_records = db.session.scalars(
            db.select(Attendance)
            .join(Student)
            .where(
                Student.course_id == course.id,
                Attendance.attendance_date == attendance_date,
            )
        ).all()
        existing_by_student = {record.student_id: record for record in existing_records}
        try:
            for student in students:
                record = existing_by_student.get(student.id)
                if record is None:
                    record = Attendance(
                        student_id=student.id, attendance_date=attendance_date
                    )
                    db.session.add(record)
                    existing_by_student[student.id] = record
                record.status = submitted[str(student.id)]
                record.remarks = request.form.get(f"remarks_{student.id}", "").strip() or None
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        flash("Attendance saved for the selected course and date.", "success")
        return redirect(
            url_for(
                "attendance.manage_attendance",
                course_id=course.id,
                attendance_date=attendance_date.isoformat(),
            )
        )

    students = []
    if course_id and attendance_date:
        students = db.session.scalars(
            db.select(Student)
            .where(Student.course_id == course_id, Student.status == "active")
            .order_by(Student.last_name, Student.first_name)
        ).all()
        existing = {
            record.student_id: record
            for record in db.session.scalars(
                db.select(Attendance)
                .join(Student)
                .where(
                    Attendance.attendance_date == attendance_date,
                    Student.course_id == course_id,
                )
            ).all()
        }
        for student in students:
            student.attendance_for_day = existing.get(student.id)

    return render_template(
        "attendance/manage.html",
        courses=courses,
        students=students,
        selected_course=course_id,
        selected_date=attendance_date or date.today(),
    )


@bp.get("/records")
@login_required
def list_attendance():
    query = (
        db.select(Attendance)
        .join(Student)
        .join(Course)
        .options(joinedload(Attendance.student).joinedload(Student.course))
        .order_by(Attendance.attendance_date.desc())
    )
    course_id = request.args.get("course_id", type=int)
    attendance_date = _read_date(request.args.get("attendance_date"))
    search = request.args.get("q", "").strip()
    if course_id:
        query = query.where(Student.course_id == course_id)
    if attendance_date:
        query = query.where(Attendance.attendance_date == attendance_date)
    if search:
        query = query.where(
            or_(
                Student.student_id.ilike(f"%{search}%"),
                Student.first_name.ilike(f"%{search}%"),
                Student.last_name.ilike(f"%{search}%"),
            )
        )
    rows = db.session.scalars(query).all()
    total = len(rows)
    present = sum(row.status == "present" for row in rows)
    percentage = round(present * 100 / total, 1) if total else 0
    return render_template(
        "attendance/list.html",
        records=rows,
        courses=db.session.scalars(db.select(Course).order_by(Course.course_name)).all(),
        percentage=percentage,
    )


@bp.post("/<int:record_pk>/delete")
@login_required
def delete_attendance(record_pk):
    record = db.get_or_404(Attendance, record_pk)
    db.session.delete(record)
    db.session.commit()
    flash("Attendance record deleted.", "success")
    return redirect(url_for("attendance.list_attendance"))


@bp.get("/summary/<int:student_pk>")
@login_required
def student_summary(student_pk):
    student = db.get_or_404(Student, student_pk)
    total = db.session.scalar(
        db.select(func.count(Attendance.id)).where(Attendance.student_id == student.id)
    ) or 0
    present = db.session.scalar(
        db.select(func.count(Attendance.id)).where(
            Attendance.student_id == student.id, Attendance.status == "present"
        )
    ) or 0
    percentage = round(present * 100 / total, 1) if total else 0
    return render_template(
        "attendance/summary.html", student=student, total=total, present=present, percentage=percentage
    )
