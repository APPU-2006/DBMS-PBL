from datetime import date

from app.extensions import db
from app.models import Course, Student


def login(client):
    client.post("/login", data={"email": "admin@sms.local", "password": "Admin@12345"})


def student_form(**overrides):
    data = {
        "student_id": "STU-002",
        "first_name": "Aarav",
        "last_name": "Sen",
        "email": "aarav@example.com",
        "phone": "+91 9876543210",
        "date_of_birth": "2005-04-12",
        "gender": "male",
        "address": "College Road",
        "course_id": "1",
        "admission_date": "2026-06-05",
        "status": "active",
    }
    data.update(overrides)
    return data


def test_student_create_list_edit_and_delete(client, app):
    login(client)
    response = client.post("/students/new", data=student_form())
    assert response.status_code == 302
    with app.app_context():
        student = db.session.scalar(
            db.select(Student).where(Student.student_id == "STU-002")
        )
        assert student is not None
        student_pk = student.id
    assert client.get("/students/").status_code == 200
    assert client.get(f"/students/{student_pk}").status_code == 200
    response = client.post(
        f"/students/{student_pk}/edit",
        data=student_form(first_name="Aarav Updated"),
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Student, student_pk).first_name == "Aarav Updated"
    response = client.post(f"/students/{student_pk}/delete")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Student, student_pk) is None


def test_student_duplicate_id_and_email_are_rejected(client, academic_data, app):
    login(client)
    response = client.post("/students/new", data=student_form(student_id="STU-001"))
    assert response.status_code == 200
    assert b"already in use" in response.data
    response = client.post(
        "/students/new",
        data=student_form(student_id="STU-003", email="anika@example.com"),
    )
    assert response.status_code == 200
    assert b"already in use" in response.data
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Student.id))) == 1


def test_invalid_course_is_rejected(client):
    login(client)
    response = client.post("/students/new", data=student_form(course_id="999"))
    assert response.status_code == 200
    assert b"Not a valid choice" in response.data


def test_empty_student_list_and_missing_record(client):
    login(client)
    assert client.get("/students/").status_code == 200
    assert client.get("/students/9999").status_code == 404


def test_student_list_pagination_with_filters(client, app):
    login(client)
    with app.app_context():
        course = db.session.scalar(db.select(Course))
        for index in range(12):
            db.session.add(
                Student(
                    student_id=f"PAGE-{index:02d}",
                    first_name=f"Student{index:02d}",
                    last_name="Page",
                    email=f"page{index}@example.com",
                    course_id=course.id,
                    admission_date=date(2026, 6, 1),
                    status="active",
                )
            )
        db.session.commit()
    response = client.get("/students/?status=active&page=2")
    assert response.status_code == 200
    assert b"Page 2 of 2" in response.data
