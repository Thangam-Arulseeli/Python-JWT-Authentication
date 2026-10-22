#### Authentication Routes   -- Now we will expose the authentication operations through FastAPI.

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User

from app.schemas.auth import (
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenInfoResponse,
    TokenResponse,
    UserResponse,
)

from app.services.auth_service import (
    AuthService,
    AuthenticationError,
    RegistrationConflict,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# --------------------------------------------------
# 1. Register a new user
# --------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    service = AuthService(db)

    try:
        user = service.register(data)

        return user

    except RegistrationConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


# --------------------------------------------------
# 2. Login
# --------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Session = Depends(get_db),
):

    service = AuthService(db)

    try:
        return service.login(
            username=form_data.username,
            password=form_data.password,
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc


# --------------------------------------------------
# 3. Refresh access token
# --------------------------------------------------

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):

    service = AuthService(db)

    try:
        return service.refresh(
            data.refresh_token
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from exc


# --------------------------------------------------
# 4. Logout
# --------------------------------------------------

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    try:
        payload = decode_token(
            data.refresh_token
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        if int(payload["sub"]) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    AuthService(db).logout(
        data.refresh_token
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


# --------------------------------------------------
# 5. Get the authenticated user
# --------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):

    return current_user


# --------------------------------------------------
# 6. Get information about the current token
# --------------------------------------------------

@router.get(
    "/token-info",
    response_model=TokenInfoResponse,
)
def get_token_info(
    current_user: User = Depends(get_current_user),
):

    return TokenInfoResponse(
        user_id=current_user.id,
        role=current_user.role,
        token_type="access",
    )


'''
Why use a form for login?
```````````````````````````
The OAuth2 password-form convention uses:

username=Admin
password=Seelicgvak@123

FastAPI receives this form data through OAuth2PasswordRequestForm.

In Swagger UI, the login endpoint will display a form rather than requiring a JSON request body.

This allows Swagger's OAuth2 password-flow interface to work with the endpoint.

For new production systems, use an appropriate modern identity flow rather than assuming the password grant is suitable for every client.


Why return a generic login error?
```````````````````````````````````
We use:

Invalid username or password.

rather than revealing whether the username exists.

This helps reduce username enumeration.

A production system should also apply rate limiting and monitoring to login attempts.

'''

