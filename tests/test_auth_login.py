"""Tests for Login & JWT authentication (Student 2).

Covers: password hashing, POST /auth/login, JWT validation, the reusable
get_current_user() dependency, and invalid / expired / forged tokens.

Run from the project root:  pytest tests/test_auth_login.py -v
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core import config
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token, decode_access_token, hash_password, verify_password
)
from app.database import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)

PASSWORD = "Shrek-Swamp-123"


@pytest.fixture(autouse=True)
def clean_users(prepared_database):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
        db.commit()


def make_user(
    email="shrek@swamp.com", username="shrek", password=PASSWORD,
    role="user", is_active=True,
) -> User:
    """Put a user straight into the database (registration is Student 1's part)."""
    with SessionLocal() as db:
        user = User(
            email=email, username=username,
            hashed_password=hash_password(password),
            role=role, is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def login(identifier="shrek@swamp.com", password=PASSWORD):
    return client.post(
        "/auth/login", data={"username": identifier, "password": password}
    )


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------- password hashing
def test_hash_is_not_the_plain_password():
    hashed = hash_password(PASSWORD)
    assert hashed != PASSWORD
    assert PASSWORD not in hashed


def test_same_password_gives_different_hashes():
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_verify_password_correct_and_wrong():
    hashed = hash_password(PASSWORD)
    assert verify_password(PASSWORD, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_very_long_and_unicode_passwords_work():
    long_password = "a" * 500
    assert verify_password(long_password, hash_password(long_password))
    unicode_password = "пароль-Шрек-🙂"
    assert verify_password(unicode_password, hash_password(unicode_password))


def test_verify_password_with_broken_hash_returns_false():
    assert verify_password(PASSWORD, "not-a-real-hash") is False


# ---------------------------------------------------------------- login
def test_login_with_email_returns_token():
    user = make_user()
    response = login("shrek@swamp.com")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert decode_access_token(body["access_token"])["sub"] == str(user.id)


def test_login_with_username_works():
    make_user()
    assert login("shrek").status_code == 200


def test_login_ignores_letter_case_of_identifier():
    make_user()
    assert login("SHREK@Swamp.COM").status_code == 200
    assert login("Shrek").status_code == 200


def test_login_wrong_password_returns_401():
    make_user()
    response = login(password="wrong-password")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_unknown_user_returns_401_with_same_message():
    make_user()
    wrong_password = login(password="wrong-password")
    unknown_user = login("nobody@swamp.com")
    assert unknown_user.status_code == 401
    # Same message: an attacker cannot tell which emails are registered.
    assert unknown_user.json() == wrong_password.json()


def test_login_password_is_case_sensitive():
    make_user()
    assert login(password=PASSWORD.lower()).status_code == 401


def test_login_missing_fields_returns_422():
    assert client.post("/auth/login", data={"username": "shrek"}).status_code == 422
    assert client.post("/auth/login", data={}).status_code == 422


def test_login_inactive_account_returns_403():
    make_user(is_active=False)
    assert login().status_code == 403


def test_login_response_never_contains_password_or_hash():
    make_user()
    text_body = login().text
    assert PASSWORD not in text_body
    assert "hashed_password" not in text_body


def test_token_payload_contains_only_safe_claims():
    make_user()
    token = login().json()["access_token"]
    payload = jwt.decode(token, options={"verify_signature": False})
    assert set(payload) == {"sub", "type", "iat", "exp"}  # no email, no password


# ------------------------------------------------- GET /auth/me + JWT checks
def test_me_with_valid_token_returns_user():
    make_user()
    token = login().json()["access_token"]
    response = client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "shrek@swamp.com"
    assert body["username"] == "shrek"
    assert body["role"] == "user"
    assert "hashed_password" not in body


def test_me_without_token_returns_401():
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_with_garbage_token_returns_401():
    response = client.get("/auth/me", headers=auth_header("not.a.token"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_me_with_wrong_scheme_returns_401():
    make_user()
    token = login().json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Basic {token}"})
    assert response.status_code == 401


def test_expired_token_returns_401():
    user = make_user()
    token = create_access_token(user.id, expires_delta=timedelta(seconds=-5))
    response = client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_token_signed_with_another_key_returns_401():
    user = make_user()
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"sub": str(user.id), "type": "access", "iat": now,
         "exp": now + timedelta(minutes=5)},
        "some-other-secret-key-that-is-long-enough-123", algorithm="HS256",
    )
    response = client.get("/auth/me", headers=auth_header(forged))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_token_with_algorithm_none_is_rejected():
    user = make_user()
    now = datetime.now(timezone.utc)
    unsigned = jwt.encode(
        {"sub": str(user.id), "type": "access", "exp": now + timedelta(minutes=5)},
        key=None, algorithm="none",
    )
    assert client.get("/auth/me", headers=auth_header(unsigned)).status_code == 401


def test_token_with_changed_payload_is_rejected():
    """Changing the user id inside the token breaks the signature."""
    make_user()
    other = make_user(email="fiona@swamp.com", username="fiona")
    token = login().json()["access_token"]
    header, payload, signature = token.split(".")
    forged_payload = jwt.encode(
        {"sub": str(other.id), "type": "access",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "x" * 40, algorithm="HS256",
    ).split(".")[1]
    forged = f"{header}.{forged_payload}.{signature}"
    assert client.get("/auth/me", headers=auth_header(forged)).status_code == 401


def _signed(payload: dict) -> str:
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def test_token_without_expiry_is_rejected():
    user = make_user()
    token = _signed({"sub": str(user.id), "type": "access"})
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_token_with_wrong_type_is_rejected():
    user = make_user()
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = _signed({"sub": str(user.id), "type": "refresh", "exp": exp})
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_token_with_non_numeric_subject_is_rejected():
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = _signed({"sub": "abc", "type": "access", "exp": exp})
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_token_of_deleted_user_returns_401():
    user = make_user()
    token = login().json()["access_token"]
    with SessionLocal() as db:
        db.execute(text("DELETE FROM users WHERE id = :i"), {"i": user.id})
        db.commit()
    response = client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 401


def test_token_of_deactivated_user_returns_403():
    user = make_user()
    token = login().json()["access_token"]
    with SessionLocal() as db:
        db.execute(text("UPDATE users SET is_active = false WHERE id = :i"),
                   {"i": user.id})
        db.commit()
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 403


def test_each_user_gets_their_own_identity():
    make_user()
    make_user(email="admin@swamp.com", username="admin", role="admin")
    shrek_token = login("shrek").json()["access_token"]
    admin_token = login("admin").json()["access_token"]
    assert client.get("/auth/me", headers=auth_header(shrek_token)).json()["role"] == "user"
    assert client.get("/auth/me", headers=auth_header(admin_token)).json()["role"] == "admin"


# --------------------------------- get_current_user() is reusable elsewhere
def test_get_current_user_protects_any_endpoint():
    """The same dependency can protect an endpoint in ANY router."""
    mini_app = FastAPI()

    @mini_app.get("/secret")
    def secret(current_user: User = Depends(get_current_user)):
        return {"hello": current_user.username}

    mini = TestClient(mini_app)
    make_user()
    token = login().json()["access_token"]
    assert mini.get("/secret").status_code == 401
    assert mini.get("/secret", headers=auth_header("bad.token.here")).status_code == 401
    ok = mini.get("/secret", headers=auth_header(token))
    assert ok.status_code == 200
    assert ok.json() == {"hello": "shrek"}


def test_swagger_authorize_button_is_configured():
    schema = client.get("/openapi.json").json()
    assert "OAuth2PasswordBearer" in schema["components"]["securitySchemes"]
