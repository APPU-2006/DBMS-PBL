from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Administrator, Course, Department, Student


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {},
            "WTF_CSRF_ENABLED": False,
            "DEMO_ADMIN_EMAIL": "admin@sms.local",
            "DEMO_ADMIN_PASSWORD": "Admin@12345",
        }
    )
    with application.app_context():
        db.create_all()
        admin = Administrator(
            full_name="Test Administrator",
            email="admin@sms.local",
            password_hash=generate_password_hash("Admin@12345"),
            is_active=True,
        )
        department = Department(
            department_code="BCA",
            department_name="Computer Applications",
        )
        db.session.add_all([admin, department])
        db.session.flush()
        course = Course(
            course_code="BCA3",
            course_name="BCA",
            department_id=department.id,
            duration_years=3,
        )
        db.session.add(course)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def academic_data(app):
    with app.app_context():
        course = db.session.scalar(db.select(Course).where(Course.course_code == "BCA3"))
        student = Student(
            student_id="STU-001",
            first_name="Anika",
            last_name="Rao",
            email="anika@example.com",
            course_id=course.id,
            admission_date=date(2026, 6, 1),
            status="active",
        )
        db.session.add(student)
        db.session.commit()
        return student.id, course.id
