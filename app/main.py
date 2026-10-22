from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.database.session import (
    Base,
    engine,
)

from app import models

from app.api.routers.auth import router as auth_router
from app.api.routers.employee import (
    router as employee_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Training setup only.
    # Use database migrations in production.
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Employee API demonstrating authentication, "
        "authorization, JWT, RBAC, and API security."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


app.include_router(auth_router)
app.include_router(employee_router)


@app.get(
    "/",
    tags=["Health"],
)
def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
    }


'''

What does CORS do?
``````````````````````
CORS stands for Cross-Origin Resource Sharing.

It controls which browser origins may read responses from an API.

Cross-Origin Resource Sharing (CORS) is a browser-enforced security mechanism that regulates how a web application running on one origin can request and access resources from a different origin. 


An origin is defined by three components: the protocol (e.g., http vs https), the domain (e.g., example.com), and the port (e.g., :80 or :3000). If any of these three elements differ between the frontend application and the destination server, the request is considered cross-origin


For example, a frontend application running on:

http://localhost:5173

may need to call the API running on:

http://localhost:8000

These are different origins, so the browser applies CORS rules.

The configuration:

allow_origins=settings.get_cors_origins()

allows only the origins listed in .env.


Is CORS authentication?
```````````````````````````
No.

CORS is a browser security mechanism, not an authentication or authorization system.

A command-line client, another backend, or a malicious non-browser client can still send requests directly to your API.

You must continue to validate credentials and enforce permissions on the server.


Why is allow_credentials=False?
-------------------------------
This training application sends Bearer tokens explicitly in the Authorization header and does not rely on browser cookies for authentication.

If you later switch to cookie-based authentication, review the CORS configuration, cookie flags, CSRF protection, and origin-validation requirements.


CSRF (Cross-Site Request Forgery) protection is a security mechanism that prevents malicious websites from forcing an authenticated user’s browser to execute unwanted, state-changing actions (such as changing a password, transferring funds, or deleting data) on a trusted web application.                                                           

'''

