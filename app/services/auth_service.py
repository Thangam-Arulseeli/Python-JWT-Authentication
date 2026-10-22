#### Authentication Service     --- File: app/services/auth_service.py
'''
The authentication service will handle:
---------------------------------------
User registration.
Password verification.
Login.
Token generation.
Refresh token persistence.
Refresh token rotation.
Logout.
Current-user lookup.

'''
from datetime import datetime, timezone

import jwt

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

from app.models.refresh_token import RefreshToken
from app.models.user import User

from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)

from app.repositories.user_repository import UserRepository

from app.schemas.auth import RegisterRequest


class AuthenticationError(Exception):
    pass


class RegistrationConflict(Exception):
    pass


class AuthService:

    def __init__(self, db: Session):
        self.db = db

        self.users = UserRepository(db)

        self.refresh_tokens = RefreshTokenRepository(db)


    def register(
        self,
        data: RegisterRequest,
    ) -> User:

        if self.users.get_by_username(data.username):
            raise RegistrationConflict(
                "Username is already registered."
            )

        if self.users.get_by_email(str(data.email)):
            raise RegistrationConflict(
                "Email is already registered."
            )

        user = User(
            username=data.username,
            email=str(data.email),
            hashed_password=hash_password(data.password),
            role="employee",
            is_active=True,
        )

        try:
            self.users.create(user)
            self.db.commit()
            self.db.refresh(user)

        except IntegrityError as exc:
            self.db.rollback()

            raise RegistrationConflict(
                "Username or email is already registered."
            ) from exc

        return user



    def authenticate(
        self,
        username: str,
        password: str,
    ) -> tuple[str, str]:

        user = self.users.get_by_username(username)

        if user is None:
            verify_password(
                password,
                DUMMY_PASSWORD_HASH,
            )

            raise AuthenticationError(
                "Invalid username or password."
            )

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise AuthenticationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise AuthenticationError(
                "Invalid username or password."
            )

        return str(user.id), user.role

  
  
    def issue_tokens(
        self,
        user_id: int,
        role: str,
    ) -> dict[str, str]:

        access_token = create_access_token(
            user_id=user_id,
            role=role,
        )

        refresh_token, jti, expires_at = (
            create_refresh_token(
                user_id=user_id,
                role=role,
            )
        )

        token_record = RefreshToken(
            jti=jti,
            token_hash=hash_refresh_token(
                refresh_token
            ),
            user_id=user_id,
            expires_at=expires_at,
            revoked=False,
        )

        self.refresh_tokens.create(token_record)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }



    def login(
        self,
        username: str,
        password: str,
    ) -> dict[str, str]:

        subject, role = self.authenticate(
            username,
            password,
        )

        tokens = self.issue_tokens(
            user_id=int(subject),
            role=role,
        )

        self.db.commit()

        return tokens



    def refresh(
        self,
        raw_refresh_token: str,
    ) -> dict[str, str]:

        try:
            payload = decode_token(raw_refresh_token)

        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            ) from exc

        if payload.get("type") != "refresh":
            raise AuthenticationError(
                "Invalid or expired refresh token."
            )

        try:
            user_id = int(payload["sub"])
        except (ValueError, TypeError, KeyError) as exc:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            ) from exc

        jti = payload.get("jti")

        if not isinstance(jti, str):
            raise AuthenticationError(
                "Invalid or expired refresh token."
            )

        token_record = self.refresh_tokens.get_valid(
            jti=jti,
            user_id=user_id,
            token_hash=hash_refresh_token(
                raw_refresh_token
            ),
        )

        if token_record is None:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            )

        user = self.users.get_by_id(user_id)

        if user is None or not user.is_active:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            )

        # Revoke the old refresh token.
        self.refresh_tokens.revoke(token_record)

        # Generate a new access token and refresh token.
        tokens = self.issue_tokens(
            user_id=user.id,
            role=user.role,
        )

        # Commit rotation atomically.
        self.db.commit()

        return tokens



    def logout(
        self,
        raw_refresh_token: str,
    ) -> None:

        try:
            payload = decode_token(raw_refresh_token)

        except jwt.InvalidTokenError:
            # Logout is idempotent for invalid tokens.
            return

        if payload.get("type") != "refresh":
            return

        try:
            user_id = int(payload["sub"])
        except (ValueError, TypeError, KeyError):
            return

        jti = payload.get("jti")

        if not isinstance(jti, str):
            return

        token_record = self.refresh_tokens.get_valid(
            jti=jti,
            user_id=user_id,
            token_hash=hash_refresh_token(
                raw_refresh_token
            ),
        )

        if token_record is not None:
            self.refresh_tokens.revoke(token_record)
            self.db.commit()

    def get_user_from_token(
        self,
        payload: dict,
    ) -> User:

        try:
            user_id = int(payload["sub"])
        except (ValueError, TypeError, KeyError) as exc:
            raise AuthenticationError(
                "Invalid authentication token."
            ) from exc

        user = self.users.get_by_id(user_id)

        if user is None or not user.is_active:
            raise AuthenticationError(
                "Invalid authentication token."
            )

        return user

    
'''
Important design note: refresh-token rotation and concurrency
----------------------------------------------------------------
The service above demonstrates token rotation, but concurrent refresh requests require additional care.

For a production implementation, perform token validation, revocation, and replacement within a properly controlled transaction. Add database-level concurrency protection, such as row locking or a conditional update that succeeds only if the token has not already been revoked.

Otherwise, two simultaneous requests could race while attempting to rotate the same refresh token.

Also consider storing a token family identifier and revoking the family if reuse of an already-rotated token is detected.
    '''

