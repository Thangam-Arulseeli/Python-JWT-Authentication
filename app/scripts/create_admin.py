#### Create the Initial Administrator
'''
Public registration must not permit users to choose the administrator role.

Therefore, create the first administrator using a trusted setup script.

'''

from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User


def main():
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()

    password = getpass("Admin password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        raise SystemExit("Passwords do not match.")

    if len(password) < 12 or len(password) > 128:
        raise SystemExit(
            "Password must be between 12 and 128 characters."
        )

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(
                (User.username == username)
                | (User.email == email)
            )
        )

        if existing:
            raise SystemExit(
                "Username or email is already registered."
            )

        admin = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True,
        )

        try:
            db.add(admin)
            db.commit()

        except IntegrityError:
            db.rollback()

            raise SystemExit(
                "Could not create administrator. "
                "Check whether the username or email already exists."
            )

    print("Administrator created successfully.")


if __name__ == "__main__":
    main()



'''
Run this only after the database has been created and the application has initialized its tables.

Why use getpass()?
```````````````````
The password is entered without being displayed in the terminal.

This is safer than typing a password directly into a command-line argument.


Corporate training discussion
```````````````````````````````

Why shouldn't we create an administrator account through a public registration endpoint?

Expected answer:

Because any unauthenticated user could attempt to register with a privileged role. Privileged account creation must be controlled by a trusted administrative process.

'''

