from authorization_service.db.base_class import Base

# Import all models here so Alembic (or metadata.create_all) can discover them
from authorization_service.models.user import User  # noqa: F401
