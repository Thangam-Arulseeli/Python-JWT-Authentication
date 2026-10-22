# DB confifuration and connation setup
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


'''
What does get_db() do?

The function creates a database session and supplies it to the API endpoint through FastAPI dependency injection.

After the request finishes, the session is closed.

The important section is:

try:
    yield db

finally:
    db.close()

This allows FastAPI to manage the dependency lifecycle.

What does pool_pre_ping=True mean?

Before using a pooled database connection, SQLAlchemy checks whether the connection is still alive.

This can help recover from stale connections.

What do pool_size and max_overflow mean?
pool_size=5: Maintain up to five persistent pooled connections.
max_overflow=10: Permit up to ten additional temporary connections under load.

These are initial training values, not universal production defaults. Tune connection pooling according to workload, database limits, and the number of application workers

'''