#### Implement Password Hashing and JWT Security
import hashlib
import uuid

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()  ### Creates a password-hashing utility configured with a recommended, secure password-hashing algorithm and settings for safely hashing and verifying passwords.

DUMMY_PASSWORD_HASH = password_hash.hash(
    "DummyPasswordForTimingOnly@123"
)


def hash_password(password: str) -> str:
    """
    Convert a plaintext password into a secure password hash.
    """

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a submitted password against its stored hash.
    """

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_token(
    user_id: int,
    role: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str, datetime]:
    """
    Generate a signed JWT.

    Returns:
        token, jti, expiration_datetime
    """

    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta

    jti = str(uuid.uuid4())

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    return token, jti, expires_at


def create_access_token(
    user_id: int,
    role: str,
) -> str:
    token, _, _ = create_token(
        user_id=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    )

    return token


def create_refresh_token(
    user_id: int,
    role: str,
) -> tuple[str, str, datetime]:
    return create_token(
        user_id=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(
            days=settings.refresh_token_expire_days
        ),
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Verify the JWT signature and expiration.

    Only the configured algorithm is accepted.
    """

    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": [
                "sub",
                "exp",
                "iat",
                "jti",
                "type",
            ],
        },
    )


def hash_refresh_token(token: str) -> str:
    """
    Create a database lookup digest for a refresh token.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

'''

Password hashing explaination
==============================

When registering a user:
`````````````````````````
hashed_password = hash_password(password)

The application generates a secure password hash.


When logging in:
```````````````````
is_valid = verify_password(
    submitted_password,
    stored_hash,
)

The password-hashing library verifies the password.

It does not decrypt the stored hash because password hashes are not intended to be decrypted.



Why not use SHA-256 for passwords?
`````````````````````````````````````
This is insufficient:

hashlib.sha256(password.encode()).hexdigest()

SHA-256 is a fast cryptographic hash. Fast hashing is undesirable for human passwords because an attacker can try many guesses quickly if the database is compromised.

Use a dedicated password-hashing algorithm such as Argon2id, configured with suitable parameters.



JWT signature validation
``````````````````````````
The following line is critical:

algorithms=[settings.jwt_algorithm]

The application explicitly allows the configured algorithm.

Do not blindly trust the algorithm specified in an unverified token header.

The decoder verifies the signature and expiration. Our application must also check the token's intended purpose, subject, and other required claims.

'''