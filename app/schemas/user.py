"""User schemas.

TEMPORARY VERSION written by Student 2 (only UserOut, needed by GET /auth/me).
Student 1 owns this file and will add UserCreate for registration.
UserOut must NEVER contain hashed_password.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
