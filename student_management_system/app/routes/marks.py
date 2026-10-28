from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.forms import MarkForm
from app.models import Course, Mark, Student

bp = Blueprint("marks", __name__)


def _populate_choices(form):
    form.student_id.choices = [
        (student.id, f"{student.student_id} - {student.full_name}")
        for student in db.session.scalars(
            db.select(Student).order_by(Student.last_name, Student.first_name)
        ).all()
    ]
    form.course_id.choices = [
        (course.id, f"{course.course_code} - {course.course_name}")
        for course in db.session.scalars(db.select(Course).order_by(Course.course_name)).all()
    ]


@bp.get("/")
@login_required
def list_marks():
    query = (
        db.select(Mark)
        .join(Student)
        .join(Course)
        .options(joinedload(Mark.student), joinedload(Mark.course))
        .order_by(Mark.exam_date.desc())
    )
    search = request.args.get("q", "").strip()
    course_id = request.args.get("course_id", type=int)
    subject = request.args.get("subject", "").strip()
    exam_type = request.args.get("exam_type", "").strip()
    if search:
        query = query.where(
            or_(
                Student.student_id.ilike(f"%{search}%"),
                Student.first_name.ilike(f"%{search}%"),
                Student.last_name.ilike(f"%{search}%"),
            )
        )
    if course_id:
        query = query.where(Mark.course_id == course_id)
    if subject:
        query = query.where(Mark.subject_name.ilike(f"%{subject}%"))
    if exam_type:
        query = query.where(Mark.exam_type.ilike(f"%{exam_type}%"))
    pagination = db.paginate(
        query, page=request.args.get("page", 1, type=int), per_page=20, error_out=False
    )
    return render_template(
        "marks/list.html",
        pagination=pagination,
        courses=db.session.scalars(db.select(Course).order_by(Course.course_name)).all(),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create_mark():
    form = MarkForm()
    _populate_choices(form)
    if not form.student_id.choices or not form.course_id.choices:
        flash("Add a student and course before recording marks.", "warning")
        return redirect(url_for("students.list_students"))
    if form.validate_on_submit():
        student = db.session.get(Student, form.student_id.data)
        if not student or student.course_id != form.course_id.data:
            form.course_id.errors.append("Select the student's enrolled course.")
        elif form.marks_obtained.data > form.maximum_marks.data:
            form.marks_obtained.errors.append("Marks cannot exceed the maximum.")
        else:
            mark = Mark(
                student_id=student.id,
                course_id=form.course_id.data,
                subject_name=form.subject_name.data.strip(),
                exam_type=form.exam_type.data.strip(),
                marks_obtained=form.marks_obtained.data,
                maximum_marks=form.maximum_marks.data,
                exam_date=form.exam_date.data,
            )
            db.session.add(mark)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("A result for this student, subject, and exam type already exists.", "danger")
            else:
                flash("Examination result recorded.", "success")
                return redirect(url_for("marks.list_marks"))
    return render_template("shared/form.html", form=form, title="Add examination marks", back_url=url_for("marks.list_marks"))


@bp.route("/<int:mark_pk>/edit", methods=["GET", "POST"])
@login_required
def edit_mark(mark_pk):
    mark = db.get_or_404(Mark, mark_pk)
    form = MarkForm(obj=mark)
    _populate_choices(form)
    if form.validate_on_submit():
        student = db.session.get(Student, form.student_id.data)
        if not student or student.course_id != form.course_id.data:
            form.course_id.errors.append("Select the student's enrolled course.")
        elif form.marks_obtained.data > form.maximum_marks.data:
            form.marks_obtained.errors.append("Marks cannot exceed the maximum.")
        else:
            mark.student_id = student.id
            mark.course_id = form.course_id.data
            mark.subject_name = form.subject_name.data.strip()
            mark.exam_type = form.exam_type.data.strip()
            mark.marks_obtained = form.marks_obtained.data
            mark.maximum_marks = form.maximum_marks.data
            mark.exam_date = form.exam_date.data
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("A result for this student, subject, and exam type already exists.", "danger")
            else:
                flash("Examination result updated.", "success")
                return redirect(url_for("marks.list_marks"))
    return render_template("shared/form.html", form=form, title="Edit examination marks", back_url=url_for("marks.list_marks"))


@bp.post("/<int:mark_pk>/delete")
@login_required
def delete_mark(mark_pk):
    mark = db.get_or_404(Mark, mark_pk)
    db.session.delete(mark)
    db.session.commit()
    flash("Examination result deleted.", "success")
    return redirect(url_for("marks.list_marks"))
