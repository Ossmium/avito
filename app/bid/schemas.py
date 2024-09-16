import uuid
import datetime
from pydantic import BaseModel, Field
from app.bid.models import BidAuthorType, BidStatusType


class BidSchema(BaseModel):
    id: uuid.UUID
    name: str
    status: BidStatusType
    author_type: BidAuthorType
    author_id: uuid.UUID
    version: int
    created_at: datetime.datetime


class BidAllFieldsSchema(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    status: BidStatusType
    tender_id: uuid.UUID
    author_type: BidAuthorType
    author_id: uuid.UUID
    version: int
    created_at: datetime.datetime


class BidCreateSchema(BaseModel):
    name: str
    description: str
    tender_id: uuid.UUID
    author_type: BidAuthorType
    author_id: uuid.UUID


class BidUpdateSchema(BaseModel):
    name: str | None = Field(None, description="Название предложения")
    description: str | None = Field(None, description="Описание предложения")


class BidDecisionSchema(BaseModel):
    id: uuid.UUID
    description: str
    created_at: datetime.datetime
