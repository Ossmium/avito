import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, TIMESTAMP, func, TEXT, ForeignKey

from app.database import Base


class OrganiztionType(Enum):
    IE = "IE"
    LLC = "LLC"
    JSC = "JSC"


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(TEXT())
    organization_type: Mapped[OrganiztionType]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class OrganizationResponsible(Base):
    __tablename__ = "organization_responsible"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"),
    )
