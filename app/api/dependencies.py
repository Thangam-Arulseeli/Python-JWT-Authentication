### Authentication and Authorization Dependencies --- File: app/api/dependencies.py

'''
This is where FastAPI's dependency injection becomes especially useful.

We will implement:

Bearer token extraction.
JWT validation.
Current-user lookup.
Role-based authorization.
Permission-based authorization.

'''

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


# OAuth2 Bearer authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"      ### This tells FastAPI to extract a Bearer token from the HTTP Authorization header.
)
### OAuth 2.0 is an industry-standard authorization protocol that tells an application what a user is allowed to do or access, not who the user is. 


# Authenticate the user using an access token
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = decode_token(token)

    except jwt.InvalidTokenError:
        raise credentials_exception

    # Accept only access tokens
    if payload.get("type") != "access":
        raise credentials_exception

    # Extract the user ID
    try:
        user_id = int(payload["sub"])

    except (ValueError, TypeError, KeyError):
        raise credentials_exception

    # Retrieve the user from the database
    user = UserRepository(db).get_by_id(user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user


# Role-based authorization
def require_roles(*allowed_roles: str):

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission "
                       "to perform this action.",
            )

        return current_user

    return role_checker


# Permission-based authorization
def require_permissions(*required_permissions: str):

    def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:

        role_permissions = {
            "admin": {
                "employee:read",
                "employee:create",
                "employee:update",
                "employee:delete",
                "user:manage",
            },
            "hr": {
                "employee:read",
                "employee:create",
                "employee:update",
            },
            "employee": {
                "employee:read",
            },
        }

        permissions = role_permissions.get(
            current_user.role,
            set(),
        )

        if not set(required_permissions).issubset(
            permissions
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return permission_checker



'''

What is OAuth2PasswordBearer?
`````````````````````````````````
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
)

This declares a Bearer token security scheme.

FastAPI uses it to:

Extract the token from the Authorization header.
Reject requests without a required Bearer token.
Add the security scheme to the OpenAPI documentation.
Display the Authorize button in Swagger UI.

The tokenUrl describes the token endpoint in the OpenAPI security scheme. It does not implement the login endpoint itself.

----------------------------------


What is Annotated?

For example:

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

This combines the expected type (User) with FastAPI dependency metadata.

When an endpoint declares:

def my_endpoint(
    current_user: CurrentUser,
):
    ...


FastAPI calls get_current_user() and supplies the authenticated user.

-------------------------------------


How does role-based access control work?
`````````````````````````````````````````
Consider:

require_roles("admin")

Only users whose database role is admin can access the endpoint.

For HR or administrators:

require_roles("admin", "hr")

This permits either role.


How does permission-based authorization work?
`````````````````````````````````````````````````````````
Instead of directly checking a role, we check whether a role has a required permission.

For example:

require_permissions("employee:create")

This is useful when multiple roles need the same permission.

Important: The role mapping in this example is defined in application code. In a larger system, roles and permissions may be managed through database tables or a centralized authorization service.

-----------------------------------------------

'''

