"""Auth tests: register, login, and protected routes."""
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User


def register(client, email="alice@example.com", password="secret123"):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def login(client, email="alice@example.com", password="secret123"):
    return client.post("/api/auth/login", data={"username": email, "password": password})


def test_register_returns_the_user_without_password(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body and "password_hash" not in body


def test_password_is_stored_hashed(client):
    register(client)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "alice@example.com"))
    assert user.password_hash != "secret123"
    assert user.password_hash.startswith("$2b$")  # bcrypt


def test_duplicate_email_is_rejected_even_with_different_case(client):
    assert register(client).status_code == 201
    response = register(client, email="ALICE@Example.com")
    assert response.status_code == 409


def test_register_validates_email_and_password(client):
    assert register(client, email="not-an-email").status_code == 422
    assert register(client, password="short").status_code == 422


def test_login_returns_a_token(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_is_case_insensitive_for_email(client):
    register(client)
    assert login(client, email="Alice@Example.COM").status_code == 200


def test_wrong_password_and_unknown_email_give_the_same_error(client):
    register(client)
    wrong_password = login(client, password="wrong-password")
    unknown_email = login(client, email="nobody@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_with_a_valid_token(client, make_user):
    headers = make_user("bob@example.com")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "bob@example.com"


def test_me_without_a_token_is_rejected(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_a_bad_token_is_rejected(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_token_of_a_deleted_user_is_rejected(client, make_user):
    headers = make_user()
    with SessionLocal() as db:
        db.delete(db.scalar(select(User)))
        db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401
