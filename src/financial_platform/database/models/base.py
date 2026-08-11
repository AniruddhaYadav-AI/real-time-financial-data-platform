from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Automatically generate table names from class names.
        (e.g., 'Instrument' -> 'instruments').
        """
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        return f"{name}s" if not name.endswith('s') else name
