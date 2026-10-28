from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.forms import StudentForm
from app.models import Course, Department, Student

bp = Blueprint("students", __name__)


def _populate_courses(form):
    form.course_id.choices = [
        (course.id, f"{course.course_code} - {course.course_name}")
        for course in db.session.scalars(
            db.select(Course).order_by(Course.course_name)
        ).all()
    ]


@bp.get("/")
@login_required
def list_students():
    query = db.select(Student).options(joinedload(Student.course).joinedload(Course.department))
    search = request.args.get("q", "").strip()
    course_id = request.args.get("course_id", type=int)
    department_id = request.args.get("department_id", type=int)
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "admission_date")
    direction = request.args.get("direction", "desc")
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Student.student_id.ilike(pattern),
                Student.first_name.ilike(pattern),
                Student.last_name.ilike(pattern),
                Student.email.ilike(pattern),
            )
        )
    if course_id:
        query = query.where(Student.course_id == course_id)
    if department_id:
        query = query.join(Course).where(Course.department_id == department_id)
    if status in {"active", "graduated", "discontinued"}:
        query = query.where(Student.status == status)
    sort_columns = {
        "student_id": Student.student_id,
        "name": Student.first_name,
        "admission_date": Student.admission_date,
        "status": Student.status,
    }
    column = sort_columns.get(sort, Student.admission_date)
    query = query.order_by(column.desc() if direction == "desc" else column.asc())
    pagination = db.paginate(
        query, page=request.args.get("page", 1, type=int), per_page=10, error_out=False
    )
    filter_args = {
        key: value for key, value in request.args.to_dict().items() if key != "page"
    }
    return render_template(
        "students/list.html",
        pagination=pagination,
        courses=db.session.scalars(db.select(Course).order_by(Course.course_name)).all(),
        departments=db.session.scalars(
            db.select(Department).order_by(Department.department_name)
        ).all(),
        filters=request.args,
        previous_page_url=url_for(
            "students.list_students", **dict(filter_args, page=pagination.prev_num)
        )
        if pagination.has_prev
        else None,
        next_page_url=url_for(
            "students.list_students", **dict(filter_args, page=pagination.next_num)
        )
        if pagination.has_next
        else None,
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create_student():
    form = StudentForm()
    _populate_courses(form)
    if not form.course_id.choices:
        flash("Create a course before enrolling students.", "warning")
        return redirect(url_for("courses.list_courses"))
    if form.validate_on_submit():
        student = Student(
            student_id=form.student_id.data.strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip() or None,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data or None,
            address=form.address.data.strip() or None,
            course_id=form.course_id.data,
            admission_date=form.admission_date.data,
            status=form.status.data,
        )
        db.session.add(student)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Student ID or email is already in use.", "danger")
        else:
            flash("Student added successfully.", "success")
            return redirect(url_for("students.list_students"))
    return render_template("students/form.html", form=form, title="Add student")


@bp.get("/<int:student_pk>")
@login_required
def details(student_pk):
    student = db.get_or_404(
        Student,
        student_pk,
        description="The requested student record was not found.",
    )
    return render_template("students/details.html", student=student)


@bp.route("/<int:student_pk>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_pk):
    student = db.get_or_404(Student, student_pk)
    form = StudentForm(obj=student)
    _populate_courses(form)
    if form.validate_on_submit():
        form.populate_obj(student)
        student.student_id = student.student_id.strip()
        student.email = student.email.strip().lower()
        student.phone = student.phone.strip() or None
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Student ID or email is already in use.", "danger")
        else:
            flash("Student details updated.", "success")
            return redirect(url_for("students.details", student_pk=student.id))
    return render_template("students/form.html", form=form, title="Edit student")


@bp.post("/<int:student_pk>/delete")
@login_required
def delete_student(student_pk):
    student = db.get_or_404(Student, student_pk)
    if student.attendance_records or student.marks:
        flash("This student has academic records and cannot be deleted. Archive them by changing status.", "warning")
    else:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted.", "success")
    return redirect(url_for("students.list_students"))
