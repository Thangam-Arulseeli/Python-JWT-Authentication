### Register Models
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.employee import Employee

__all__ = [
    "User",
    "RefreshToken",
    "Employee",
]


'''
This imports all models in one place.

Later, we will import this package before calling:

Base.metadata.create_all(bind=engine)

That ensures SQLAlchemy has registered the models before creating the tables.

Production note: create_all() is suitable for simple initial application. It is not a substitute for database migrations. Production applications should use a migration tool such as Alembic.

'''