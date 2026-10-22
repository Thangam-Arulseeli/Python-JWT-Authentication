### Define Pydantic Schemas --- File: app/schemas/auth.py

#### Schemas define which fields clients can submit and which fields the application returns.

### They are separate from database models.

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )

    email: EmailStr

    password: str = Field(
        min_length=12,
        max_length=128,
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: Literal["admin", "hr", "employee"]
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        min_length=20,
        max_length=4096,
    )


class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        min_length=20,
        max_length=4096,
    )


class TokenInfoResponse(BaseModel):
    user_id: int
    role: str
    token_type: str



'''
Important validation concepts
==================================
Consider:

username: str = Field(
    min_length=3,
    max_length=50,
    pattern=r"^[A-Za-z0-9_.-]+$",
)

This means:

The username must be at least three characters.
It cannot exceed fifty characters.
It can contain only the specified characters.


Email validation
```````````````````
email: EmailStr     --- Pydantic validates the email format.

It does not prove that the email address exists or belongs to the user.

Consider:
password: str = Field(
    min_length=12,
    max_length=128,
)

This imposes a minimum length and a maximum length.

A complete password policy should also account for breached-password screening, usability, rate limiting, and the selected password-hashing algorithm's input constraints.


Critical security decision: do not accept a role during registration
```````````````````````````````````````````````````````````````````````
Notice that RegisterRequest does not contain a role field.

A client must not be able to register as an administrator by submitting:

{
  "username": "attacker",
  "email": "attacker@example.com",
  "password": "LongPassword@123",
  "role": "admin"
}

The schema will reject the unexpected field under Pydantic's default extra-field handling.

Even if a request includes additional data, the service must assign the role itself.

We will set the role to employee in the registration service.

'''


