"""Tests for user registration: POST /auth/register (Assignment 7, Student 1).

They run on the separate PostgreSQL TEST database (see tests/conftest.py).
Run from the project root:  pytest tests/test_auth_register.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.database import SessionLocal
from app.main import app
from app.models.user import User
from app.services import auth_service

client = TestClient(app)

URL = "/auth/register"


@pytest.fixture(autouse=True)
def empty_users_table(prepared_database):
    """Start every test with no users."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
        db.commit()


def make_payload(**changes):
    payload = {
        "email": "shrek@swamp.com",
        "username": "shrek",
        "password": "Fiona-1234",
    }
    payload.update(changes)
    return payload


def count_users() -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(User))


# ---------------------------------------------------------------------------
# Successful registration
# ---------------------------------------------------------------------------

def test_register_success():
    response = client.post(URL, json=make_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["email"] == "shrek@swamp.com"
    assert body["username"] == "shrek"
    assert body["role"] == "user"
    assert body["created_at"]
    assert set(body) == {"id", "email", "username", "role", "created_at"}


def test_password_is_stored_as_hash_not_plain_text():
    password = "Fiona-1234"
    client.post(URL, json=make_payload(password=password))

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "shrek"))

    assert user.hashed_password != password
    assert password not in user.hashed_password
    assert user.hashed_password.startswith("$argon2id$")
    assert verify_password(password, user.hashed_password) is True


def test_response_does_not_expose_password_or_hash():
    response = client.post(URL, json=make_payload(password="Fiona-1234"))
    text_body = response.text
    assert "Fiona-1234" not in text_body
    assert "password" not in text_body.lower()
    assert "argon2" not in text_body


def test_two_different_users_can_register():
    first = client.post(URL, json=make_payload())
    second = client.post(
        URL,
        json=make_payload(email="donkey@swamp.com", username="donkey"),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert count_users() == 2


def test_email_is_stored_in_lowercase():
    response = client.post(URL, json=make_payload(email="Shrek@Swamp.COM"))
    assert response.status_code == 201
    assert response.json()["email"] == "shrek@swamp.com"


# ---------------------------------------------------------------------------
# Duplicates -> 409
# ---------------------------------------------------------------------------

def test_duplicate_email_returns_409():
    client.post(URL, json=make_payload())
    response = client.post(URL, json=make_payload(username="another_name"))
    assert response.status_code == 409
    assert "Email" in response.json()["detail"]
    assert count_users() == 1


def test_duplicate_username_returns_409():
    client.post(URL, json=make_payload())
    response = client.post(URL, json=make_payload(email="other@swamp.com"))
    assert response.status_code == 409
    assert "Username" in response.json()["detail"]
    assert count_users() == 1


def test_duplicate_email_with_different_letter_case_returns_409():
    client.post(URL, json=make_payload())
    response = client.post(
        URL, json=make_payload(email="SHREK@SWAMP.COM", username="other")
    )
    assert response.status_code == 409
    assert count_users() == 1


def test_database_unique_constraint_is_the_final_protection(monkeypatch):
    """Simulate a race: both friendly checks say 'free', but the DB says no.

    The API must still answer 409, hide database details, roll back, and keep
    working for the next request.
    """
    client.post(URL, json=make_payload())
    monkeypatch.setattr(auth_service, "_exists", lambda db, column, value: False)

    duplicate_email = client.post(URL, json=make_payload(username="other"))
    duplicate_name = client.post(URL, json=make_payload(email="other@swamp.com"))

    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["detail"] == "Email is already registered"
    assert duplicate_name.status_code == 409
    assert duplicate_name.json()["detail"] == "Username is already taken"
    for response in (duplicate_email, duplicate_name):
        lowered = response.text.lower()
        assert "constraint" not in lowered
        assert "insert" not in lowered
        assert "postgres" not in lowered

    ok = client.post(
        URL, json=make_payload(email="donkey@swamp.com", username="donkey")
    )
    assert ok.status_code == 201
    assert count_users() == 2


def test_database_rejects_duplicate_rows_directly():
    with SessionLocal() as db:
        db.add(User(email="a@x.com", username="a_user", hashed_password="h"))
        db.commit()
        db.add(User(email="a@x.com", username="b_user", hashed_password="h"))
        with pytest.raises(IntegrityError):
            db.commit()


# ---------------------------------------------------------------------------
# Invalid input -> 422
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_email", ["not-an-email", "shrek@", "@swamp.com", ""])
def test_invalid_email_is_rejected(bad_email):
    response = client.post(URL, json=make_payload(email=bad_email))
    assert response.status_code == 422
    assert count_users() == 0


def test_too_short_password_is_rejected():
    response = client.post(URL, json=make_payload(password="short1"))
    assert response.status_code == 422
    assert count_users() == 0


def test_password_of_only_spaces_is_rejected():
    response = client.post(URL, json=make_payload(password=" " * 10))
    assert response.status_code == 422


def test_too_long_password_is_rejected():
    response = client.post(URL, json=make_payload(password="a" * 129))
    assert response.status_code == 422


@pytest.mark.parametrize("bad_username", ["", "ab", "a" * 31, "has space", "bad!name"])
def test_invalid_username_is_rejected(bad_username):
    response = client.post(URL, json=make_payload(username=bad_username))
    assert response.status_code == 422
    assert count_users() == 0


@pytest.mark.parametrize("missing", ["email", "username", "password"])
def test_missing_field_is_rejected(missing):
    payload = make_payload()
    del payload[missing]
    assert client.post(URL, json=payload).status_code == 422


def test_client_cannot_choose_its_own_role():
    response = client.post(URL, json=make_payload(role="admin"))
    assert response.status_code == 422
    assert count_users() == 0


# ---------------------------------------------------------------------------
# Password helper (app/core/security.py)
# ---------------------------------------------------------------------------

def test_verify_password_accepts_correct_password():
    hashed = hash_password("Fiona-1234")
    assert verify_password("Fiona-1234", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("Fiona-1234")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_broken_hash():
    assert verify_password("Fiona-1234", "this-is-not-a-hash") is False


def test_same_password_gets_different_hashes():
    """Every hash has its own random salt."""
    assert hash_password("Fiona-1234") != hash_password("Fiona-1234")
