from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    jti: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


    '''
Why keep refresh tokens in the database?

A stateless JWT access token can be verified using its signature and claims.

However, a refresh token needs a revocation mechanism if we want logout and token rotation to invalidate previously issued refresh credentials.

The database allows us to:

Check whether a refresh token has been revoked.
Prevent a token from being reused after rotation.
Revoke a refresh token during logout.
Track which user owns a token.
Enforce token expiration.


Why store token_hash?
`````````````````````
We store a SHA-256 digest of the refresh token rather than the original bearer credential.

Because refresh tokens are generated with high entropy, a cryptographic digest is suitable for identifying the exact token without keeping its raw value in the database.

This is different from password storage: passwords require a slow password-hashing algorithm such as Argon2 because human-selected passwords have limited entropy.

    '''