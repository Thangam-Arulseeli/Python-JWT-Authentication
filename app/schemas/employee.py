from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class EmployeeCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    department: str = Field(
        min_length=2,
        max_length=100,
    )


class EmployeeUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    department: str = Field(
        min_length=2,
        max_length=100,
    )


class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    department: str
    created_by: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

'''
These schemas prevent clients from submitting arbitrary database fields.

For example, a client cannot directly specify created_by during employee creation.

The server derives it from the authenticated user's identity.
'''