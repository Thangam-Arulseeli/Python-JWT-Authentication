### Create Repository Classes
### User repository     --- File: app/repositories/user_repository.py
### The repository layer contains database operations.

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(
            User.id == user_id
        )

        return self.db.scalar(statement)


    def get_by_username(
        self,
        username: str,
    ) -> User | None:
        statement = select(User).where(
            User.username == username
        )

        return self.db.scalar(statement)


    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            User.email == email
        )

        return self.db.scalar(statement)


    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()

        return user

'''
db.flush() sends pending changes to the database within the current transaction, allowing the database-generated ID to become available.

It does not commit the transaction.

That allows the service layer to decide when to commit.
'''

 
