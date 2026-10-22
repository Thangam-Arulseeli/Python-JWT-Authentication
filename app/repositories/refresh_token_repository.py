### Refresh token repository  --- File: app/repositories/refresh_token_repository.py

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_valid(
        self,
        jti: str,
        user_id: int,
        token_hash: str,
    ) -> RefreshToken | None:
        statement = select(RefreshToken).where(
            RefreshToken.jti == jti,
            RefreshToken.user_id == user_id,
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at
            > datetime.now(timezone.utc),
        )

        return self.db.scalar(statement)


    def create(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.flush()

        return refresh_token


    def revoke(
        self,
        refresh_token: RefreshToken,
    ) -> None:
        refresh_token.revoked = True
        self.db.flush()


'''

The token's jti, user ID, digest, expiration, and revocation status are checked.

This prevents a refresh token from being accepted merely because its JWT signature is valid.

'''