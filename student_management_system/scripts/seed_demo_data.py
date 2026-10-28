import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import Administrator, Attendance, Course, Department, Mark, Student


def seed():
    app = create_app()
    with app.app_context():
        if not db.engine.dialect.name.startswith("mysql") and not app.config["TESTING"]:
            raise RuntimeError("Demo data seeding must use the configured MySQL database.")
        try:
            administrator = db.session.scalar(
                db.select(Administrator).where(
                    Administrator.email == app.config["DEMO_ADMIN_EMAIL"].lower()
                )
            )
            if administrator is None:
                administrator = Administrator(
                    full_name="SMS Demo Administrator",
                    email=app.config["DEMO_ADMIN_EMAIL"].strip().lower(),
                    role="admin",
                    is_active=True,
                )
                administrator.set_password(app.config["DEMO_ADMIN_PASSWORD"])
                db.session.add(administrator)

            department_data = [
                ("BCA", "Computer Applications", "Computing and software studies."),
                ("BCOM", "Commerce", "Commerce and business studies."),
                ("BBA", "Business Administration", "Management studies."),
            ]
            departments = {}
            for code, name, description in department_data:
                department = db.session.scalar(
                    db.select(Department).where(Department.department_code == code)
                )
                if department is None:
                    department = Department(
                        department_code=code,
                        department_name=name,
                        description=description,
                    )
                    db.session.add(department)
                    db.session.flush()
                departments[code] = department

            course_data = [
                ("BCA3", "Bachelor of Computer Applications", "BCA", 3),
                ("BCOM3", "Bachelor of Commerce", "BCOM", 3),
                ("BBA3", "Bachelor of Business Administration", "BBA", 3),
            ]
            courses = {}
            for code, name, department_code, years in course_data:
                course = db.session.scalar(
                    db.select(Course).where(Course.course_code == code)
                )
                if course is None:
                    course = Course(
                        course_code=code,
                        course_name=name,
                        department_id=departments[department_code].id,
                        duration_years=years,
                        description="Fictional demonstration course.",
                    )
                    db.session.add(course)
                    db.session.flush()
                courses[code] = course

            students = []
            given_names = [
                "Aarav", "Asha", "Dev", "Diya", "Ishan",
                "Kavya", "Mira", "Neel", "Riya", "Vihaan",
            ]
            family_names = [
                "Sharma", "Rao", "Patel", "Nair", "Das",
                "Mehta", "Iyer", "Khan", "Joshi", "Sen",
            ]
            course_codes = list(courses)
            for index in range(10):
                student_id = f"SMS{2026}{index + 1:03d}"
                student = db.session.scalar(
                    db.select(Student).where(Student.student_id == student_id)
                )
                if student is None:
                    student = Student(
                        student_id=student_id,
                        first_name=given_names[index],
                        last_name=family_names[index],
                        email=f"student{index + 1}@example.com",
                        phone=f"+91 90000 {index + 1:00000}",
                        course_id=courses[course_codes[index % len(course_codes)]].id,
                        admission_date=date(2026, 6, 1) + timedelta(days=index),
                        status="active",
                    )
                    db.session.add(student)
                    db.session.flush()
                students.append(student)

            today = date.today()
            for student in students:
                for days_ago in (2, 1, 0):
                    attendance_date = today - timedelta(days=days_ago)
                    record = db.session.scalar(
                        db.select(Attendance).where(
                            Attendance.student_id == student.id,
                            Attendance.attendance_date == attendance_date,
                        )
                    )
                    if record is None:
                        record = Attendance(
                            student_id=student.id,
                            attendance_date=attendance_date,
                            status=("absent" if student.id % 5 == 0 else "present"),
                        )
                        db.session.add(record)
                existing_mark = db.session.scalar(
                    db.select(Mark).where(
                        Mark.student_id == student.id,
                        Mark.subject_name == "Database Management Systems",
                        Mark.exam_type == "Internal Assessment 1",
                    )
                )
                if existing_mark is None:
                    db.session.add(
                        Mark(
                            student_id=student.id,
                            course_id=student.course_id,
                            subject_name="Database Management Systems",
                            exam_type="Internal Assessment 1",
                            marks_obtained=70 + (student.id % 25),
                            maximum_marks=100,
                            exam_date=today - timedelta(days=7),
                        )
                    )
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        print(f"Seed complete. Admin email: {app.config['DEMO_ADMIN_EMAIL']}")
        print("Run this script again safely; existing demo records are retained.")


if __name__ == "__main__":
    seed()
