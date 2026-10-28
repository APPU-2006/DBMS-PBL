from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Attendance, Course, Department, Mark, Student


def login(client):
    client.post("/login", data={"email": "admin@sms.local", "password": "Admin@12345"})


def test_department_course_creation_and_safe_deletion(client, app):
    login(client)
    response = client.post(
        "/departments/new",
        data={"department_code": "SCI", "department_name": "Science", "description": ""},
    )
    assert response.status_code == 302
    response = client.post(
        "/courses/new",
        data={
            "course_code": "SCI1",
            "course_name": "Science",
            "department_id": "2",
            "duration_years": "3",
            "description": "",
        },
    )
    assert response.status_code == 302
    response = client.post("/departments/2/delete")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Department, 2) is not None
        assert db.session.scalar(db.select(Course).where(Course.course_code == "SCI1"))


def test_bulk_attendance_upserts_and_summary(client, app, academic_data):
    login(client)
    student_id, course_id = academic_data
    target_date = "2026-10-28"
    payload = {
        "course_id": str(course_id),
        "attendance_date": target_date,
        f"status_{student_id}": "present",
        f"remarks_{student_id}": "",
    }
    assert client.post("/attendance/", data=payload).status_code == 302
    payload[f"status_{student_id}"] = "late"
    assert client.post("/attendance/", data=payload).status_code == 302
    with app.app_context():
        records = db.session.scalars(
            db.select(Attendance).where(Attendance.student_id == student_id)
        ).all()
        assert len(records) == 1
        assert records[0].status == "late"
        records[0].status = "present"
        db.session.commit()
    response = client.get(f"/attendance/summary/{student_id}")
    assert b"100.0%" in response.data


def test_attendance_percentage_handles_no_records(client, academic_data):
    login(client)
    student_id, _ = academic_data
    response = client.get(f"/attendance/summary/{student_id}")
    assert response.status_code == 200
    assert b"0%" in response.data


def test_duplicate_attendance_constraint(app, academic_data):
    student_id, _ = academic_data
    with app.app_context():
        db.session.add_all(
            [
                Attendance(student_id=student_id, attendance_date=date(2026, 10, 1), status="present"),
                Attendance(student_id=student_id, attendance_date=date(2026, 10, 1), status="absent"),
            ]
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.scalar(db.select(db.func.count(Attendance.id))) == 0


def test_marks_validation_grade_and_persistence(client, app, academic_data):
    login(client)
    student_id, course_id = academic_data
    payload = {
        "student_id": str(student_id),
        "course_id": str(course_id),
        "subject_name": "DBMS",
        "exam_type": "Internal",
        "marks_obtained": "85",
        "maximum_marks": "100",
        "exam_date": "2026-10-01",
    }
    assert client.post("/marks/new", data=payload).status_code == 302
    with app.app_context():
        mark = db.session.scalar(db.select(Mark))
        assert mark is not None
        assert mark.percentage == Decimal("85")
        assert mark.grade == "A"
        mark_pk = mark.id
    assert client.get("/marks/").status_code == 200
    assert client.get(f"/marks/{mark_pk}/edit").status_code == 200
    payload["subject_name"] = "DBMS 2"
    payload["marks_obtained"] = "101"
    response = client.post("/marks/new", data=payload)
    assert response.status_code == 200
    assert b"cannot exceed" in response.data


def test_duplicate_marks_business_constraint(app, academic_data):
    student_id, course_id = academic_data
    first = Mark(
        student_id=student_id,
        course_id=course_id,
        subject_name="DBMS",
        exam_type="Internal",
        marks_obtained=Decimal("70"),
        maximum_marks=Decimal("100"),
        exam_date=date(2026, 10, 1),
    )
    second = Mark(
        student_id=student_id,
        course_id=course_id,
        subject_name="DBMS",
        exam_type="Internal",
        marks_obtained=Decimal("75"),
        maximum_marks=Decimal("100"),
        exam_date=date(2026, 10, 2),
    )
    with app.app_context():
        db.session.add_all([first, second])
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.scalar(db.select(db.func.count(Mark.id))) == 0


def test_reports_dashboard_and_not_found(client):
    login(client)
    assert client.get("/dashboard").status_code == 200
    assert client.get("/reports/").status_code == 200
    assert client.get("/not-a-route").status_code == 404


def test_management_pages_render(client, academic_data):
    login(client)
    _, course_id = academic_data
    pages = (
        "/departments/",
        "/departments/new",
        "/courses/",
        "/courses/new",
        f"/courses/{course_id}/students",
        f"/attendance/?course_id={course_id}&attendance_date=2026-10-28",
        "/attendance/records",
        "/marks/",
        "/marks/new",
        "/reports/",
        "/reports/students.csv",
    )
    for path in pages:
        assert client.get(path).status_code == 200, path
