from fastapi import APIRouter
from sqlalchemy import insert

from app.database import async_session_maker
from app.organization.models import Organization, OrganizationResponsible
from app.organization.schemas import OrganizationSchema, OrganizationResponsibleSchema

router = APIRouter(prefix="/organizations", tags=["Organization"])


@router.post("/new", include_in_schema=False)
async def create_organization(organization: OrganizationSchema):
    async with async_session_maker() as session:
        query = insert(Organization).values(
            name=organization.name,
            description=organization.description,
            organization_type=organization.organization_type,
        )
        await session.execute(query)
        await session.commit()


@router.post("/organization_responsible/new", include_in_schema=False)
async def create_organization_responsible(
    organization_responsible: OrganizationResponsibleSchema,
):
    async with async_session_maker() as session:
        query = insert(OrganizationResponsible).values(
            organization_id=organization_responsible.organization_id,
            user_id=organization_responsible.user_id,
        )
        await session.execute(query)
        await session.commit()
