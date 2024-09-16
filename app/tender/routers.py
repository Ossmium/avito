import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, insert, or_, and_, update
from sqlalchemy.exc import NoResultFound, IntegrityError

from app.database import async_session_maker
from app.user.models import User
from app.organization.models import Organization, OrganizationResponsible
from app.tender.models import (
    Tender,
    TenderVersion,
    TenderServiceType,
    TenderStatusType,
)
from app.tender.schemas import (
    TenderSchema,
    TenderCreateSchema,
    TenderAllFieldsSchema,
    TenderUpdate,
)

router = APIRouter(
    prefix="/tenders",
    tags=["Tenders"],
)


@router.get("")
async def get_tenders(
    username: str,
    limit: int = 5,
    offset: int = 0,
    service_type: TenderServiceType = None,
) -> list[TenderSchema]:
    """
    Список тендеров с возможностью фильтрации по типу услуг.

    Если фильтры не заданы, возвращаются все тендеры доступные пользователю ответсвенному за органиизацию и со статусом Published.
    """

    async with async_session_maker() as session:
        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        subquery = (
            select(Tender.id)
            .join(
                OrganizationResponsible,
                Tender.organization_id == OrganizationResponsible.organization_id,
            )
            .where(OrganizationResponsible.user_id == user.id)
            .subquery()
        )

        query = select(Tender).where(
            or_(
                Tender.id.in_(subquery),
                Tender.status == TenderStatusType.Published,
            )
        )

        if service_type:
            query = query.where(Tender.service_type == service_type).order_by(
                Tender.name
            )

        query = query.limit(limit).offset(offset)

        result = await session.execute(query)

        return result.scalars().all()


@router.post("/new")
async def create_tender(tender: TenderCreateSchema) -> TenderAllFieldsSchema:
    """
    Создание нового тендера с заданными параметрами.
    """

    async with async_session_maker() as session:
        user_query = select(User).where(User.username == tender.creator_username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        org_resp_query = select(OrganizationResponsible).filter(
            OrganizationResponsible.organization_id == tender.organization_id,
            OrganizationResponsible.user_id == user.id,
        )
        org_resp = await session.execute(org_resp_query)
        org_resp = org_resp.scalars().all()

        if len(org_resp) < 1:
            raise HTTPException(
                status_code=401,
                detail="Такой организации нет",
            )

        query = (
            insert(Tender)
            .values(
                name=tender.name,
                description=tender.description,
                service_type=tender.service_type,
                status=tender.status,
                organization_id=tender.organization_id,
                creator_username=tender.creator_username,
            )
            .returning(Tender)
        )
        try:
            result = await session.execute(query)
        except IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="Тендер с таким названием уже существует",
            )
        await session.commit()

        tender_db = result.scalar_one()

        new_version_query = insert(TenderVersion).values(
            name=tender_db.name,
            description=tender_db.description,
            service_type=tender_db.service_type,
            status=tender_db.status,
            organization_id=tender_db.organization_id,
            creator_username=tender_db.creator_username,
            version=tender_db.version,
            tender_id=tender_db.id,
        )
        await session.execute(new_version_query)
        await session.commit()

        return tender_db


@router.get("/my")
async def get_user_tenders(
    username: str, limit: int = 5, offset: int = 0
) -> list[TenderSchema]:
    """
    Получение списка тендеров текущего пользователя.

    Для удобства использования включена поддержка пагинации.
    """

    async with async_session_maker() as session:
        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        query = (
            select(Tender)
            .where(Tender.creator_username == username)
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()


@router.get("/{tender_id}/status")
async def get_tender_status(
    tender_id: uuid.UUID,
    username: str,
) -> TenderStatusType | None:
    """
    Получить статус тендера по его уникальному идентификатору.
    """

    async with async_session_maker() as session:
        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        query = (
            select(Tender.status)
            .join(
                OrganizationResponsible,
                Tender.organization_id == OrganizationResponsible.organization_id,
            )
            .where(
                or_(
                    and_(
                        Tender.id == tender_id,
                        OrganizationResponsible.user_id == user.id,
                    ),
                    Tender.status == TenderStatusType.Published,
                )
            )
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()


@router.put("/{tender_id}/status")
async def change_tender_status(
    tender_id: uuid.UUID,
    status: TenderStatusType,
    username: str,
):
    """
    Получить статус тендера по его уникальному идентификатору.
    """

    async with async_session_maker() as session:
        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        query = (
            select(Tender)
            .join(
                OrganizationResponsible,
                Tender.organization_id == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    Tender.id == tender_id,
                    OrganizationResponsible.user_id == user.id,
                )
            )
        )

        result = await session.execute(query)

        try:
            tender = result.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Данного тендера не существует",
            )

        update_query = (
            update(Tender)
            .values(
                status=status,
                version=Tender.version + 1,
            )
            .where(Tender.id == tender_id)
            .returning(Tender)
        )
        updated_tender = await session.execute(update_query)
        await session.commit()
        updated_tender = updated_tender.scalar_one_or_none()

        new_version_query = insert(TenderVersion).values(
            name=updated_tender.name,
            description=updated_tender.description,
            service_type=updated_tender.service_type,
            status=updated_tender.status,
            organization_id=updated_tender.organization_id,
            creator_username=updated_tender.creator_username,
            version=updated_tender.version,
            tender_id=updated_tender.id,
        )
        await session.execute(new_version_query)
        await session.commit()

        return updated_tender.status


@router.patch("/{tender_id}/edit")
async def edit_tender(
    tender_id: uuid.UUID,
    username: str,
    tender_update: TenderUpdate = None,
) -> TenderSchema:
    async with async_session_maker() as session:
        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        query = (
            select(Tender)
            .join(
                OrganizationResponsible,
                Tender.organization_id == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    Tender.id == tender_id,
                    OrganizationResponsible.user_id == user.id,
                )
            )
        )

        result = await session.execute(query)

        try:
            tender = result.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Данного тендера не существует",
            )

        update_values = {}
        for key, value in tender_update:
            if value != "" or value is not None:
                update_values[key] = value

        if update_values:
            update_query = (
                update(Tender)
                .where(Tender.id == tender_id)
                .values(
                    **update_values,
                    version=Tender.version + 1,
                )
                .returning(Tender)
            )
            new_version_query = insert(TenderVersion).values(
                name=tender.name
                if "name" not in update_values.keys()
                else update_values["name"],
                description=tender.description
                if "description" not in update_values.keys()
                else update_values["description"],
                service_type=tender.service_type
                if "service_type" not in update_values.keys()
                else update_values["service_type"],
                status=tender.status,
                organization_id=tender.organization_id,
                creator_username=tender.creator_username,
                version=tender.version + 1,
                tender_id=tender.id,
            )
            updated_tender = await session.execute(update_query)
            await session.execute(new_version_query)
            await session.commit()

            return updated_tender.scalar_one_or_none()
        else:
            return tender


@router.put("/{tender_id}/rollback/{version}")
async def tender_rollback(
    tender_id: uuid.UUID,
    version: int,
    username: str,
):
    async with async_session_maker() as session:
        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        query = (
            select(TenderVersion)
            .join(
                OrganizationResponsible,
                TenderVersion.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    TenderVersion.tender_id == tender_id,
                    OrganizationResponsible.user_id == user.id,
                    TenderVersion.version == version,
                )
            )
        )

        result = await session.execute(query)

        try:
            tender_version = result.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Данного тендера не существует",
            )

        update_tender_query = (
            update(Tender)
            .values(
                name=tender_version.name,
                description=tender_version.description,
                service_type=tender_version.service_type,
                status=tender_version.status,
                organization_id=tender_version.organization_id,
                version=Tender.version + 1,
                creator_username=tender_version.creator_username,
            )
            .where(Tender.id == tender_id)
            .returning(Tender)
        )
        updated_tender = await session.execute(update_tender_query)
        await session.commit()
        updated_tender = updated_tender.scalar_one()

        new_version_query = insert(TenderVersion).values(
            name=updated_tender.name,
            description=updated_tender.description,
            service_type=updated_tender.service_type,
            status=updated_tender.status,
            organization_id=updated_tender.organization_id,
            creator_username=updated_tender.creator_username,
            version=updated_tender.version,
            tender_id=updated_tender.id,
        )
        await session.execute(new_version_query)
        await session.commit()

        return updated_tender
