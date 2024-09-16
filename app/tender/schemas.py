import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.tender.models import TenderServiceType, TenderStatusType


class TenderSchema(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    service_type: TenderServiceType
    status: TenderStatusType
    version: int
    created_at: datetime


class TenderCreateSchema(BaseModel):
    name: str
    description: str
    service_type: TenderServiceType
    status: TenderStatusType
    organization_id: uuid.UUID
    creator_username: str


class TenderAllFieldsSchema(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    service_type: TenderServiceType
    status: TenderStatusType
    organization_id: uuid.UUID
    version: int
    creator_username: str
    created_at: datetime


class TenderUpdate(BaseModel):
    name: str | None = Field(None, description="Название тендера")
    description: str | None = Field(None, description="Описание тендера")
    service_type: str | None = Field(
        None, description="Тип услуги", example="Construction"
    )
