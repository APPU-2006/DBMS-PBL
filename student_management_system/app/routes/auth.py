from urllib.parse import urljoin, urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm
from app.models import Administrator

bp = Blueprint("auth", __name__)


def _safe_redirect_target(target):
    if not target:
        return None
    if "\\" in target or target.startswith("//"):
        return None
    base = urlsplit(request.host_url)
    candidate = urlsplit(urljoin(request.host_url, target))
    if (
        candidate.scheme not in ("http", "https")
        or candidate.netloc != base.netloc
    ):
        return None
    return target


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        administrator = db.session.scalar(
            db.select(Administrator).where(Administrator.email == email)
        )
        if (
            administrator
            and administrator.is_active
            and administrator.check_password(form.password.data)
        ):
            login_user(administrator, remember=form.remember.data)
            target = _safe_redirect_target(request.args.get("next"))
            return redirect(target or url_for("dashboard.index"))
        flash("The email or password is incorrect, or this account is inactive.", "danger")
    return render_template("login.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
