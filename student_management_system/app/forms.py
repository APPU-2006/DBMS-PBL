import re

from flask_wtf import FlaskForm
from wtforms.validators import ValidationError
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp


def _administrator_email(form, field):
    value = field.data or ""
    if value.lower().endswith("@sms.local"):
        local_part = value.rsplit("@", 1)[0]
        if (
            value.count("@") != 1
            or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+", local_part)
            or local_part.startswith(".")
            or local_part.endswith(".")
            or ".." in local_part
        ):
            raise ValidationError("Enter a valid email address.")
        return
    Email()(form, field)


class LoginForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), _administrator_email, Length(max=254)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class StudentForm(FlaskForm):
    student_id = StringField(
        "Student ID", validators=[DataRequired(), Length(max=30)]
    )
    first_name = StringField(
        "First name", validators=[DataRequired(), Length(max=80)]
    )
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=80)])
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(max=254)]
    )
    phone = StringField(
        "Phone",
        validators=[
            Optional(),
            Length(max=30),
            Regexp(r"^[0-9+().\-\s]+$", message="Enter a valid phone number."),
        ],
    )
    date_of_birth = DateField("Date of birth", validators=[Optional()], format="%Y-%m-%d")
    gender = SelectField(
        "Gender",
        choices=[("", "Prefer not to say"), ("female", "Female"), ("male", "Male"), ("other", "Other")],
        validators=[Optional()],
    )
    address = TextAreaField("Address", validators=[Optional(), Length(max=2000)])
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    admission_date = DateField(
        "Admission date", validators=[DataRequired()], format="%Y-%m-%d"
    )
    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("graduated", "Graduated"),
            ("discontinued", "Discontinued"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save student")


class DepartmentForm(FlaskForm):
    department_code = StringField(
        "Department code", validators=[DataRequired(), Length(max=20)]
    )
    department_name = StringField(
        "Department name", validators=[DataRequired(), Length(max=120)]
    )
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save department")


class CourseForm(FlaskForm):
    course_code = StringField("Course code", validators=[DataRequired(), Length(max=20)])
    course_name = StringField("Course name", validators=[DataRequired(), Length(max=150)])
    department_id = SelectField("Department", coerce=int, validators=[DataRequired()])
    duration_years = IntegerField(
        "Duration (years)", validators=[DataRequired(), NumberRange(min=1, max=20)]
    )
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save course")


class MarkForm(FlaskForm):
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    subject_name = StringField("Subject", validators=[DataRequired(), Length(max=120)])
    exam_type = StringField("Exam type", validators=[DataRequired(), Length(max=60)])
    marks_obtained = DecimalField(
        "Marks obtained", places=2, validators=[DataRequired(), NumberRange(min=0)]
    )
    maximum_marks = DecimalField(
        "Maximum marks", places=2, validators=[DataRequired(), NumberRange(min=0.01)]
    )
    exam_date = DateField("Exam date", validators=[DataRequired()], format="%Y-%m-%d")
    submit = SubmitField("Save marks")
