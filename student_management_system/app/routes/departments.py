from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.forms import DepartmentForm
from app.models import Course, Department

bp = Blueprint("departments", __name__)


@bp.get("/")
@login_required
def list_departments():
    search = request.args.get("q", "").strip()
    query = db.select(Department).order_by(Department.department_name)
    if search:
        query = query.where(
            or_(
                Department.department_code.ilike(f"%{search}%"),
                Department.department_name.ilike(f"%{search}%"),
            )
        )
    departments = db.session.scalars(query).all()
    return render_template("departments/list.html", departments=departments)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(
            department_code=form.department_code.data.strip().upper(),
            department_name=form.department_name.data.strip(),
            description=form.description.data.strip() or None,
        )
        db.session.add(department)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Department code and name must both be unique.", "danger")
        else:
            flash("Department added.", "success")
            return redirect(url_for("departments.list_departments"))
    return render_template("shared/form.html", form=form, title="Add department", back_url=url_for("departments.list_departments"))


@bp.route("/<int:department_pk>/edit", methods=["GET", "POST"])
@login_required
def edit_department(department_pk):
    department = db.get_or_404(Department, department_pk)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        department.department_code = form.department_code.data.strip().upper()
        department.department_name = form.department_name.data.strip()
        department.description = form.description.data.strip() or None
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Department code and name must both be unique.", "danger")
        else:
            flash("Department updated.", "success")
            return redirect(url_for("departments.list_departments"))
    return render_template("shared/form.html", form=form, title="Edit department", back_url=url_for("departments.list_departments"))


@bp.post("/<int:department_pk>/delete")
@login_required
def delete_department(department_pk):
    department = db.get_or_404(Department, department_pk)
    if department.courses:
        flash("Move or remove this department's courses before deleting it.", "warning")
    else:
        db.session.delete(department)
        db.session.commit()
        flash("Department deleted.", "success")
    return redirect(url_for("departments.list_departments"))
