"""Authentication settings, read from the .env file.

Add these lines to your .env (see .env.example):

    SECRET_KEY=<a long random string>
    ACCESS_TOKEN_EXPIRE_MINUTES=30

Create a secret key with:
    python -c "import secrets; print(secrets.token_hex(32))"
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Same .env file that app/database.py reads.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Add it to .env (see .env.example). "
        "Create one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# HS256 = the token is signed with one shared secret key.
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
