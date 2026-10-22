#### Employee Service       -- File: app/services/employee_service.py

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.employee_repository import (
    EmployeeRepository,
)

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
)


class EmployeeNotFound(Exception):
    pass


class EmployeeConflict(Exception):
    pass


class EmployeeService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = EmployeeRepository(db)

    def get_all(self) -> list[Employee]:
        return self.repository.get_all()


    def get_by_id(
        self,
        employee_id: int,
    ) -> Employee:

        employee = self.repository.get_by_id(
            employee_id
        )

        if employee is None:
            raise EmployeeNotFound(
                "Employee not found."
            )

        return employee


    def create(
        self,
        data: EmployeeCreate,
        created_by: int,
    ) -> Employee:

        if self.repository.get_by_email(
            str(data.email)
        ):
            raise EmployeeConflict(
                "Employee email already exists."
            )

        employee = Employee(
            name=data.name,
            email=str(data.email),
            department=data.department,
            created_by=created_by,
        )

        try:
            self.repository.create(employee)
            self.db.commit()
            self.db.refresh(employee)

        except IntegrityError as exc:
            self.db.rollback()

            raise EmployeeConflict(
                "Employee email already exists."
            ) from exc

        return employee



    def update(
        self,
        employee_id: int,
        data: EmployeeUpdate,
    ) -> Employee:

        employee = self.get_by_id(employee_id)

        existing = self.repository.get_by_email(
            str(data.email)
        )

        if existing is not None and existing.id != employee.id:
            raise EmployeeConflict(
                "Employee email already exists."
            )

        employee.name = data.name
        employee.email = str(data.email)
        employee.department = data.department

        try:
            self.db.commit()
            self.db.refresh(employee)

        except IntegrityError as exc:
            self.db.rollback()

            raise EmployeeConflict(
                "Employee email already exists."
            ) from exc

        return employee



    def delete(
        self,
        employee_id: int,
    ) -> None:

        employee = self.get_by_id(employee_id)

        self.repository.delete(employee)

        self.db.commit()


    '''
Why put business logic in a service?
---------------------------------------
The router should not contain all the database logic.

For example:

employee = service.create(
    data=data,
    created_by=current_user.id,
)

The service handles the actual business operation.

This separation improves testability, readability, and maintainability.
    '''