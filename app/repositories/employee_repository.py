### Employee repository     --- File: app/repositories/employee_repository.py

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employee import Employee


class EmployeeRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_all(self) -> list[Employee]:
        statement = select(Employee).order_by(
            Employee.id
        )

        return list(
            self.db.scalars(statement).all()
        )


    def get_by_id(
        self,
        employee_id: int,
    ) -> Employee | None:
        statement = select(Employee).where(
            Employee.id == employee_id
        )

        return self.db.scalar(statement)


    def get_by_email(
        self,
        email: str,
    ) -> Employee | None:
        statement = select(Employee).where(
            Employee.email == email
        )

        return self.db.scalar(statement)


    def create(self, employee: Employee) -> Employee:
        self.db.add(employee)
        self.db.flush()

        return employee


    def delete(self, employee: Employee) -> None:
        self.db.delete(employee)
        self.db.flush()

    '''
We use SQLAlchemy's select() syntax rather than older query patterns.

The database access remains separate from HTTP routing.
'''