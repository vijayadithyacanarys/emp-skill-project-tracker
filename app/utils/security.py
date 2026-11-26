from datetime import datetime, timedelta, timezone
import os
import uuid

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash
load_dotenv()


password_hash = PasswordHash.recommended()
MIN_SECRET_LENGTH = 32
SUPPORTED_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})


class JWTConfigurationError(RuntimeError):
    pass


def _jwt_config() -> tuple[str, str]:
    secret = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM")

    if not secret:
        raise JWTConfigurationError("JWT SECRET_KEY is not configured")
    if len(secret.strip()) < MIN_SECRET_LENGTH:
        raise JWTConfigurationError(
            f"JWT SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters"
        )
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise JWTConfigurationError(
            "JWT ALGORITHM must be one of HS256, HS384, or HS512"
        )
    return secret, algorithm


def hashed_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def create_access_token(
    user_id: uuid.UUID,
    credential_version: uuid.UUID,
) -> str:
    secret, algorithm = _jwt_config()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

    claims = {
        "exp": expiry,
        "sub": str(user_id),
        "credential_version": str(credential_version),
    }
    return jwt.encode(claims, secret, algorithm=algorithm)


def verify_access_token(token: str) -> dict:
    secret, algorithm = _jwt_config()
    return jwt.decode(
        token,
        secret,
        algorithms=[algorithm],
        options={
            "require": ["exp", "sub", "credential_version"],
            "verify_exp": True,
            "verify_signature": True,
        },
    )
