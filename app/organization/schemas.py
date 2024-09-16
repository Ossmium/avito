import uuid
from pydantic import BaseModel

from app.organization.models import OrganiztionType


class OrganizationSchema(BaseModel):
    name: str
    description: str
    organization_type: OrganiztionType


class OrganizationResponsibleSchema(BaseModel):
    organization_id: uuid.UUID
    user_id: uuid.UUID
