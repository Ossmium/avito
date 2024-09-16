import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import (
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    func,
)

from app.database import Base


class TenderServiceType(Enum):
    Construction = "Construction"
    Delivery = "Delivery"
    Manufacture = "Manufacture"


class TenderStatusType(Enum):
    Created = "Created"
    Published = "Published"
    Closed = "Closed"


class Tender(Base):
    __tablename__ = "tender"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text())
    service_type: Mapped[TenderServiceType]
    status: Mapped[TenderStatusType] = mapped_column(
        default=TenderStatusType.Created,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
    )
    version: Mapped[int] = mapped_column(default=1)
    creator_username: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )

    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="tender")

    __table_args__ = (
        CheckConstraint(
            "version > 0",
            name="check_version_minimum",
        ),
    )


class TenderVersion(Base):
    __tablename__ = "tender_version"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text())
    service_type: Mapped[TenderServiceType]
    status: Mapped[TenderStatusType]
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
    )
    version: Mapped[int] = mapped_column(default=1)
    creator_username: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tender.id", ondelete="CASCADE"),
    )

    __table_args__ = (
        CheckConstraint(
            "version > 0",
            name="check_version_minimum",
        ),
    )
