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
    Index,
    UniqueConstraint,
)

from app.database import Base


class BidStatusType(Enum):
    Created = "Created"
    Published = "Published"
    Canceled = "Canceled"


class BidDecisionType(Enum):
    Approved = "Approved"
    Rejected = "Rejected"


class BidAuthorType(Enum):
    Organization = "Organization"
    User = "User"


class Bid(Base):
    __tablename__ = "bid"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text())
    status: Mapped[BidStatusType] = mapped_column(
        default=BidStatusType.Created,
    )
    author_type: Mapped[BidAuthorType]
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"),
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tender.id", ondelete="CASCADE"),
    )
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )

    tender: Mapped["Tender"] = relationship("Tender", back_populates="bids")

    __table_args__ = (
        CheckConstraint(
            "version > 0",
            name="check_version_minimum",
        ),
        UniqueConstraint(
            "name",
            "description",
            "author_type",
            "author_id",
            name="uq_tender_bid",
        ),
    )


class BidVersion(Base):
    __tablename__ = "bid_version"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text())
    status: Mapped[BidStatusType]
    author_type: Mapped[BidAuthorType]
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"),
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tender.id", ondelete="CASCADE"),
    )
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )
    bid_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bid.id", ondelete="CASCADE"),
    )

    __table_args__ = (
        CheckConstraint(
            "version > 0",
            name="check_version_minimum",
        ),
    )


class BidReview(Base):
    __tablename__ = "bid_review"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    description: Mapped[str] = mapped_column(String(1000))
    bid_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bid.id", ondelete="CASCADE"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )


class BidDecision(Base):
    __tablename__ = "bid_decision"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    bid_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bid.id", ondelete="CASCADE"),
    )
    decision: Mapped[BidDecisionType]
    username: Mapped[str] = mapped_column(String(50))


class BidResponsible(Base):
    __tablename__ = "bid_responsible"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    bid_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bid.id", ondelete="CASCADE"),
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=True,
    )
