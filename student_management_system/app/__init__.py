import logging
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import IntegrityError

from app.extensions import csrf, db, login_manager, migrate


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set SECRET_KEY in your .env before starting the application.")
    os.makedirs(app.instance_path, exist_ok=True)

    logging.basicConfig(level=logging.INFO)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models
    from app.routes import register_blueprints

    register_blueprints(app)

    @app.route("/")
    def index():
        from flask_login import current_user

        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500

    @app.errorhandler(OperationalError)
    def database_unavailable(error):
        db.session.rollback()
        app.logger.error("Database operation failed: %s", error.__class__.__name__)
        if request.path.startswith("/static/"):
            raise error
        flash(
            "The database is currently unavailable. Check your MySQL service and configuration.",
            "danger",
        )
        return render_template("errors/database.html"), 503

    @app.errorhandler(IntegrityError)
    def integrity_conflict(error):
        db.session.rollback()
        app.logger.warning("Database integrity conflict: %s", error.__class__.__name__)
        return render_template("errors/conflict.html"), 409

    return app
