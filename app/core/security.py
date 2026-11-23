"""Password hashing helpers (Argon2id).

Reusable by the whole team:

    from app.core.security import hash_password, verify_password

Student 2 uses verify_password() in the login endpoint.

A hash is one-way: you cannot turn it back into the password. Every hash
also contains its own random salt, so hashing the same password twice gives
two different strings - that is normal.
"""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# PasswordHasher() uses Argon2id with safe default settings.
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash that is safe to store in the database."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the stored hash, else False.

    Never raises for a wrong password or a broken hash - it just returns False.
    """
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError):
        # VerifyMismatchError (wrong password) is a kind of VerificationError.
        return False
