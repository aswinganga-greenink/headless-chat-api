from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy models.
    Automatic table naming and common columns.
    """
    id: Any
    __name__: str

    # Generate __tablename__ automatically from class name
    # e.g., 'User' -> 'user', 'UserProfile' -> 'user_profile' (if logic was complex),
    # keeping it simple: lowercase of class name.
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Common timestamps for all models
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
