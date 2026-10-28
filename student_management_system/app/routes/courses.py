from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.forms import CourseForm
from app.models import Course, Department, Mark, Student

bp = Blueprint("courses", __name__)


def _populate_departments(form):
    form.department_id.choices = [
        (department.id, department.department_name)
        for department in db.session.scalars(
            db.select(Department).order_by(Department.department_name)
        ).all()
    ]


@bp.get("/")
@login_required
def list_courses():
    query = (
        db.select(Course, func.count(Student.id))
        .outerjoin(Student, Student.course_id == Course.id)
        .group_by(Course.id)
        .order_by(Course.course_name)
    )
    search = request.args.get("q", "").strip()
    department_id = request.args.get("department_id", type=int)
    if search:
        query = query.where(
            or_(Course.course_code.ilike(f"%{search}%"), Course.course_name.ilike(f"%{search}%"))
        )
    if department_id:
        query = query.where(Course.department_id == department_id)
    return render_template(
        "courses/list.html",
        courses=db.session.execute(query).all(),
        departments=db.session.scalars(db.select(Department).order_by(Department.department_name)).all(),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create_course():
    form = CourseForm()
    _populate_departments(form)
    if not form.department_id.choices:
        flash("Create a department before creating courses.", "warning")
        return redirect(url_for("departments.create_department"))
    if form.validate_on_submit():
        course = Course(
            course_code=form.course_code.data.strip().upper(),
            course_name=form.course_name.data.strip(),
            department_id=form.department_id.data,
            duration_years=form.duration_years.data,
            description=form.description.data.strip() or None,
        )
        db.session.add(course)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Course code must be unique and the department must exist.", "danger")
        else:
            flash("Course added.", "success")
            return redirect(url_for("courses.list_courses"))
    return render_template("shared/form.html", form=form, title="Add course", back_url=url_for("courses.list_courses"))


@bp.route("/<int:course_pk>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_pk):
    course = db.get_or_404(Course, course_pk)
    form = CourseForm(obj=course)
    _populate_departments(form)
    if form.validate_on_submit():
        course.course_code = form.course_code.data.strip().upper()
        course.course_name = form.course_name.data.strip()
        course.department_id = form.department_id.data
        course.duration_years = form.duration_years.data
        course.description = form.description.data.strip() or None
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Course code must be unique and the department must exist.", "danger")
        else:
            flash("Course updated.", "success")
            return redirect(url_for("courses.list_courses"))
    return render_template("shared/form.html", form=form, title="Edit course", back_url=url_for("courses.list_courses"))


@bp.get("/<int:course_pk>/students")
@login_required
def course_students(course_pk):
    course = db.get_or_404(Course, course_pk)
    students = db.session.scalars(
        db.select(Student).where(Student.course_id == course.id).order_by(Student.last_name)
    ).all()
    return render_template("courses/students.html", course=course, students=students)


@bp.post("/<int:course_pk>/delete")
@login_required
def delete_course(course_pk):
    course = db.get_or_404(Course, course_pk)
    if course.students or course.marks:
        flash("This course has enrolled students or examination records and cannot be deleted.", "warning")
    else:
        db.session.delete(course)
        db.session.commit()
        flash("Course deleted.", "success")
    return redirect(url_for("courses.list_courses"))
