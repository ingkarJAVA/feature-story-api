"""Schemas for the login response."""
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until the token expires
