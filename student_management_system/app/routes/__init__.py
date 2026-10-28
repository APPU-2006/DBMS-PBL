def register_blueprints(app):
    from app.routes.attendance import bp as attendance_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.courses import bp as courses_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.departments import bp as departments_bp
    from app.routes.marks import bp as marks_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.students import bp as students_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp, url_prefix="/students")
    app.register_blueprint(departments_bp, url_prefix="/departments")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(marks_bp, url_prefix="/marks")
    app.register_blueprint(reports_bp, url_prefix="/reports")
