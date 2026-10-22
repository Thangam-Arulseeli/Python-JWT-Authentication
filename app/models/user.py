from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="employee",
        server_default="employee",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


    '''
Why store hashed_password rather than password?

Never store plaintext passwords.

For example, this is unsafe:

username: admin
password: Admin@12345

Instead, the database stores an Argon2 hash.

A stored hash might look like:

$argon2id$v=19$m=65536,t=3,p=4$...

The actual hash contains the information needed for password verification, including the salt and algorithm parameters.

It does not reveal the original password directly.


Why is username unique?
-----------------------------
The database constraint prevents two accounts from having the same username.

This is important because application-level checks alone are not sufficient to prevent duplicates when concurrent requests arrive.
The database must enforce uniqueness.


Why does role default to employee?
--------------------------------
A publicly registered user must not be allowed to choose their own privileged role.

We will enforce this in the registration schema and service.

Only a trusted administrative operation should create or promote privileged users.
    '''