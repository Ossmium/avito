import uuid
from datetime import datetime
from sqlalchemy import String, TIMESTAMP, func
from sqlalchemy.orm import mapped_column, Mapped

from app.database import Base


class User(Base):
    __tablename__ = "employee"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
