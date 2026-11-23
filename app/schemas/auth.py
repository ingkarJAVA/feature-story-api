"""Pydantic schemas for user registration (Assignment 7, Student 1)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Data required to create an account.

    extra="forbid" means a client cannot send extra fields such as
    "role": "admin" - the request is rejected with 422.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(description="A valid email address")
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="3-30 characters: letters, digits, '_', '.' or '-'",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="8-128 characters",
    )

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        # "Shrek@Swamp.com" and "shrek@swamp.com" must be the same account.
        return value.lower()

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be only spaces")
        return value


class UserResponse(BaseModel):
    """Public information about a user.

    There is deliberately NO password and NO hashed_password field here,
    so they can never leak in an API response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: str
    created_at: datetime
