from app.extensions import db
from app.models import Administrator


def test_login_logout(client):
    response = client.post(
        "/login",
        data={"email": "admin@sms.local", "password": "Admin@12345"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert client.get("/dashboard").status_code == 200
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_invalid_credentials_and_inactive_admin(client, app):
    response = client.post(
        "/login", data={"email": "admin@sms.local", "password": "incorrect"}
    )
    assert response.status_code == 200, response.location
    assert b"incorrect" in response.data.lower()
    with app.app_context():
        admin = db.session.scalar(
            db.select(Administrator).where(Administrator.email == "admin@sms.local")
        )
        admin.is_active = False
        db.session.commit()
    response = client.post(
        "/login", data={"email": "admin@sms.local", "password": "Admin@12345"}
    )
    assert response.status_code == 200, response.location
    assert b"inactive" in response.data.lower()


def test_protected_routes_redirect_without_login(client):
    for path in (
        "/dashboard",
        "/students/",
        "/departments/",
        "/courses/",
        "/attendance/",
        "/marks/",
        "/reports/",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_login_rejects_external_redirect(client):
    response = client.post(
        "/login?next=https://example.com/",
        data={"email": "admin@sms.local", "password": "Admin@12345"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_login_requires_csrf_token(client, app):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post(
        "/login", data={"email": "admin@sms.local", "password": "Admin@12345"}
    )
    assert response.status_code == 400
