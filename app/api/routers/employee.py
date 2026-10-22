### Employee Routes with RBAC   ---- File: app/api/routers/employees.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.api.dependencies import (
    require_permissions,
    require_roles,
)

from app.database.session import get_db
from app.models.user import User

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

from app.services.employee_service import (
    EmployeeConflict,
    EmployeeNotFound,
    EmployeeService,
)


router = APIRouter(
    prefix="/api/employees",
    tags=["Employees"],
)


# --------------------------------------------------
# 1. List employees
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[EmployeeResponse],
)
def list_employees(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permissions("employee:read")
    ),

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):

    employees = EmployeeService(db).get_all()

    # Simple paginat
    # ion.
    # For production, apply LIMIT in the database query.
    return employees[:limit]


# --------------------------------------------------
# 2. Get employee by ID
# --------------------------------------------------

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permissions("employee:read")
    ),
):

    try:
        return EmployeeService(db).get_by_id(
            employee_id
        )

    except EmployeeNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        ) from exc


# --------------------------------------------------
# 3. Create employee
# --------------------------------------------------

@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permissions("employee:create")
    ),
):

    try:
        return EmployeeService(db).create(
            data=data,
            created_by=current_user.id,
        )

    except EmployeeConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


# --------------------------------------------------
# 4. Update employee
# --------------------------------------------------

@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permissions("employee:update")
    ),
):

    try:
        return EmployeeService(db).update(
            employee_id=employee_id,
            data=data,
        )

    except EmployeeNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        ) from exc

    except EmployeeConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


# --------------------------------------------------
# 5. Delete employee
# --------------------------------------------------

@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("admin")
    ),
):

    try:
        EmployeeService(db).delete(
            employee_id
        )

    except EmployeeNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        ) from exc

    return None



'''
What security controls are being applied?
````````````````````````````````````````````
List employees
`````````````````
Depends(require_permissions("employee:read"))

An authenticated user needs the employee:read permission.


Create employees
`````````````````
Depends(
    require_permissions("employee:create")
)

Only roles with employee-creation permission can proceed.

In our mapping, these are admin and hr.


Delete employees
`````````````````
Depends(require_roles("admin"))

Only an administrator can delete an employee.

Validate query parameters
limit: int = Query(
    default=20,
    ge=1,
    le=100,
)

This rejects invalid limits such as zero, negative values, and values above 100.


Important performance note
```````````````````````````````
The example applies the limit after retrieving the records to keep the code straightforward for training.

For production, apply pagination in the database query itself.

For example, the repository should use SQLAlchemy's .limit() and .offset() or an appropriate keyset-pagination strategy.

'''


