import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.config import settings

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def authenticate_moderator(username: str, password: str) -> bool:
    # Always verify the password so timing does not reveal whether the username matched.
    password_ok = password_hash.verify(password, settings.moderator_password_hash)
    username_ok = secrets.compare_digest(
        username.encode(),
        settings.moderator_username.encode(),
    )
    return username_ok and password_ok


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_moderator(token: str = Depends(oauth2_scheme)) -> str:
    """Reusable dependency for future moderator endpoints."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise credentials_error

    subject = str(payload["sub"])
    username_ok = secrets.compare_digest(
        subject.encode(),
        settings.moderator_username.encode(),
    )
    if not username_ok:
        raise credentials_error
    return subject
