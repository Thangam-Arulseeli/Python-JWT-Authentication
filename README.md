JWT Authendication and Authorizaion
======================================

Objectives
----------- 
Explain authentication versus authorization.
Understand password hashing and securely store passwords.
Implement user registration and login.
Generate and validate JWT access tokens.
Implement refresh tokens and token renewal.
Use OAuth2 Password Bearer concepts with FastAPI.
Protect APIs using Bearer authentication.
Implement role-based access control (RBAC).
Enforce permissions for different user roles.
Configure CORS correctly.
Manage application secrets using environment variables.
Validate incoming API requests using Pydantic.
Prevent common authentication and authorization vulnerabilities.
Test secured endpoints using Swagger UI.
Understand important OWASP API Security risks.

======================================================

Application scenario
=========================
We will develop a small Employee Management API with Authentication and Authorization.

Consider the following employees and roles
----------------------------------------
User	    Role	    Permissions
--------------------------------------
Admin	    admin	    Create employees, view employees, update employees,         
                        delete employees, manage users
HR Manager	hr	        Create employees, view employees, update employees
Employee	employee	View employee information and access permitted personal 
                        resources

The application will provide these features:
--------------------------------------------------------------------------------
Feature	                Endpoint	                        Authentication
--------------------------------------------------------------------------------
Register a user	        POST /api/auth/register	            Public
Login	                POST /api/auth/login	            Public
Refresh access token	POST /api/auth/refresh	             Valid refresh token
Get current user	    GET /api/auth/me	                Required
List employees	        GET /api/employees/	                Required
View employee	        GET /api/employees/{employee_id}	Required
Create employee	        POST /api/employees/	            Admin or HR
Update employee	        PUT /api/employees/{employee_id}	Admin or HR
Delete employee	        DELETE /api/employees/{employee_id}	Admin only
Inspect token payload	GET /api/auth/token-info	        Required


We will also implement logout by revoking refresh tokens.

Important: The implementation below is a application designed to demonstrate the complete authentication flow. It includes several production-oriented safeguards, but a real deployment requires additional controls such as HTTPS, rate limiting, centralized audit logging, key rotation, operational monitoring, and a carefully designed token-revocation strategy.

===================================================

Authentication vs. Authorization

===================================================


Application Architecture
-----------------------------
We will use FastAPI, PostgreSQL, SQLAlchemy 2.x, Pydantic, and JWT.

The application follows this architecture:

                 Swagger UI
                     |
                     v
              FastAPI Routers
                     |
                     v
             Authentication Layer
                     |
          +----------+-----------+
          |                      |
          v                      v
    Token Validation       Permission Checks
          |                      |
          +----------+-----------+
                     |
                     v
               Service Layer
                     |
                     v
             Repository Layer
                     |
                     v
                SQLAlchemy
                     |
                     v
                PostgreSQL

==================================

Project folder structure
----------------------------
Create a project named Python_JWT_Authentication

Python_JWT_Authentication   [fastapi_secure_api]
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   └── employee.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── employee.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── refresh_token_repository.py
│   │   └── employee_repository.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── employee_service.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── employees.py
│   │
│   └── scripts/
│       ├── __init__.py
│       └── create_admin.py
│
├── .env
├── .gitignore
└── requirements.txt


Why use this structure?
============================
Component	             Responsibility
------------------------------------------------------
main.py	                Creates the FastAPI application and registers middleware and 
                        routers
core/config.py	        Loads application settings and secrets
core/security.py	    Password hashing, JWT creation, and JWT validation
database/session.py	    SQLAlchemy engine, session factory, and database dependency
models/	                Database tables
schemas/	            Request and response validation
repositories/	        Database queries
services/	            Business logic
api/dependencies.py	    Current-user authentication and authorization
api/routers/	        HTTP endpoints
scripts/create_admin.py	Creates the initial administrator securely

Create empty __init__.py files in the listed Python package directories.

============================================================

Create the Python Environment
-----------------------------------
Open a terminal in the project directory.

    > mkdir Python-JWT-Authentication
    > cd Python-JWT-Authentication

    > py -m venv venv
 
    > .\venv\Scripts\Activate.ps1

If PowerShell blocks script activation, you can invoke the environment's Python directly:

    > .\venv\Scripts\python.exe --version

---------------------

Create requirements.txt
------------------------------
Why are these packages required?

Package	                        Purpose
---------------------------------------------
fastapi	                        Web API framework
uvicorn	                        ASGI server
sqlalchemy	                    ORM and database access
psycopg[binary]	                PostgreSQL driver
pydantic[email]	                Data validation and email validation
pydantic-settings	            Configuration management
PyJWT	                        JWT creation and verification
pwdlib[argon2]              	Secure password hashing
python-multipart	            Processes OAuth2 username/password form data


Note: We use Argon2 password hashing instead of storing plaintext passwords or using a fast general-purpose hash such as SHA-256.

OAuth 2.0 is an industry-standard authorization protocol that tells an application what a user is allowed to do or access, not who the user is. 

Password hashing and JWT signing solve different problems:
-------------------------------------------
Password hashing protects stored passwords.
JWT signing protects the integrity of token claims.


Install the packages
    > python -m pip install -r requirements.txt

-----------------------------------

Configure PostgreSQL
-------------------------
Make sure PostgreSQL is installed and its database server is running.

Using pgAdmin, create a database:

CREATE DATABASE Python-JWT-Authentication [secure_api_db];

The database should be accessible through your PostgreSQL server.

For a local installation, the connection settings might be:

Host: 127.0.0.1
Port: 5432
Database: Python-JWT-Authendication
Username: postgres


Use your actual PostgreSQL credentials.
======================================

Set .env file configuration settings for 
    DatabaseURL
    JWT_SECRET_KEY
    JWT_ALGORITHM

    ACCESS_TOKEN_EXPIRE_MINUTES=15
    REFRESH_TOKEN_EXPIRE_DAYS=7

    CORS_ORIGINS

=======================================

Generate a random JWT secret
----------------------------
Run:

python -c "import secrets; print(secrets.token_urlsafe(48))"

Copy the generated value into JWT_SECRET_KEY.

Do not use a predictable value such as:

JWT_SECRET_KEY=secret123

Do not commit .env to source contro

-------------------------------------------

Create .gitignore file

=================================


Create the Database Models

We need three main types of database records:

Users
Refresh tokens
Employees

Each has a separate SQLAlchemy model.

9.1 User model
File: app/models/user.py


9.2. Refresh token model
File: app/models/refresh_token.py

9.3 Employee model
File: app/models/employee.py


10. Step 6 — Register Models
File: app/models/__init__.py



