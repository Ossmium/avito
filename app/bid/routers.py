import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import insert, select, or_, and_, update

from app.bid.models import (
    Bid,
    BidReview,
    BidVersion,
    BidDecision,
    BidResponsible,
    BidAuthorType,
    BidStatusType,
    BidDecisionType,
)
from app.user.models import User
from app.tender.models import Tender, TenderStatusType
from app.organization.models import OrganizationResponsible, Organization
from app.database import async_session_maker
from app.bid.schemas import (
    BidCreateSchema,
    BidSchema,
    BidAllFieldsSchema,
    BidUpdateSchema,
    BidDecisionSchema,
)

router = APIRouter(
    prefix="/bids",
    tags=["Bids"],
)


@router.post("/new")
async def create_bid(bid: BidCreateSchema) -> BidSchema:
    async with async_session_maker() as session:
        get_tender_query = select(Tender).where(
            Tender.id == bid.tender_id,
            Tender.status == TenderStatusType.Published,
        )
        tender = await session.execute(get_tender_query)

        try:
            tender = tender.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого тендера нет",
            )

        user_query = select(User).where(User.id == bid.author_id)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )
        organization_resp = None
        if bid.author_type == BidAuthorType.Organization:
            get_organization_query = select(OrganizationResponsible).where(
                OrganizationResponsible.user_id == bid.author_id
            )
            organization_resp = await session.execute(get_organization_query)

            try:
                organization_resp = organization_resp.scalar_one()
            except NoResultFound:
                raise HTTPException(
                    status_code=401,
                    detail="Данной организации нет",
                )

            if organization_resp.organization_id == tender.organization_id:
                raise HTTPException(
                    status_code=401,
                    detail="Нельзя создать предложение от имени своей организации для своей организации",
                )

        create_bid_query = (
            insert(Bid)
            .values(
                name=bid.name,
                description=bid.description,
                author_type=bid.author_type,
                tender_id=bid.tender_id,
                status=BidStatusType.Created,
                author_id=bid.author_id,
            )
            .returning(Bid)
        )

        try:
            bid_db = await session.execute(create_bid_query)
        except IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="Данное предложение уже было создано для тендера",
            )
        await session.commit()
        bid_db = bid_db.scalar_one()

        create_bid_resp_query = insert(
            BidResponsible,
        ).values(
            bid_id=bid_db.id,
            organization_id=organization_resp.organization_id
            if organization_resp is not None
            else None,
        )

        create_bid_version_query = insert(BidVersion).values(
            name=bid_db.name,
            description=bid_db.description,
            author_type=bid_db.author_type,
            tender_id=bid_db.tender_id,
            status=BidStatusType.Created,
            author_id=bid_db.author_id,
            bid_id=bid_db.id,
        )
        await session.execute(create_bid_version_query)
        await session.execute(create_bid_resp_query)
        await session.commit()

        return bid_db


@router.get("/my")
async def get_user_bids(username: str, limit: int = 5, offset: int = 0):
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
            select(Bid)
            .where(
                Bid.author_id == user.id,
            )
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()


@router.get("/{tender_id}/list")
async def get_tender_bids(
    tender_id: uuid.UUID,
    username: str,
    limit: int = 5,
    offset: int = 0,
) -> list[BidSchema]:
    async with async_session_maker() as session:
        get_tender_query = select(Tender).where(
            and_(
                Tender.id == tender_id,
                or_(
                    Tender.status == TenderStatusType.Published,
                    Tender.status == TenderStatusType.Closed,
                ),
            )
        )
        tender = await session.execute(get_tender_query)

        try:
            tender = tender.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Такого тендера нет",
            )

        user_query = select(User).where(User.username == username)
        user = await session.execute(user_query)
        try:
            user = user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        subquery_main = (
            select(Bid)
            .select_from(Bid)
            .join(
                BidResponsible,
                Bid.id == BidResponsible.bid_id,
            )
            .outerjoin(
                OrganizationResponsible,
                BidResponsible.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    Bid.tender_id == tender_id,
                    or_(
                        OrganizationResponsible.user_id == user.id,
                        and_(
                            Bid.author_id == user.id,
                            Bid.author_type == BidAuthorType.User,
                        ),
                        Bid.status == BidStatusType.Published,
                    ),
                ),
            )
            .limit(6)
            .offset(offset)
        )
        subquery_publish = select(Bid).where(
            Bid.status == BidStatusType.Published,
        )

        query = subquery_main.union(subquery_publish)

        bids = await session.execute(query)

        return bids.mappings().all()


@router.get("/{bid_id}/status")
async def get_bid_status(
    bid_id: uuid.UUID,
    username: str,
) -> BidStatusType:
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

        get_bid_query = (
            select(Bid)
            .select_from(Bid)
            .join(
                BidResponsible,
                Bid.id == BidResponsible.bid_id,
            )
            .outerjoin(
                OrganizationResponsible,
                BidResponsible.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    Bid.id == bid_id,
                    or_(
                        OrganizationResponsible.user_id == user.id,
                        and_(
                            Bid.author_id == user.id,
                            Bid.author_type == BidAuthorType.User,
                        ),
                    ),
                ),
            )
        )
        bid = await session.execute(get_bid_query)

        try:
            bid = bid.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Такого предложения нет",
            )

        return bid.status


@router.put("/{bid_id}/status")
async def edit_bid_status(
    bid_id: uuid.UUID,
    status: BidStatusType,
    username: str,
) -> BidSchema:
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

        get_bid_query = (
            select(Bid)
            .select_from(Bid)
            .join(
                BidResponsible,
                Bid.id == BidResponsible.bid_id,
            )
            .outerjoin(
                OrganizationResponsible,
                BidResponsible.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    Bid.id == bid_id,
                    or_(
                        OrganizationResponsible.user_id == user.id,
                        and_(
                            Bid.author_id == user.id,
                            Bid.author_type == BidAuthorType.User,
                        ),
                    ),
                ),
            )
        )
        bid = await session.execute(get_bid_query)

        try:
            bid = bid.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Такого предложения нет",
            )

        if bid.status != status:
            update_bid_query = (
                update(Bid)
                .values(
                    status=status,
                    version=Bid.version + 1,
                )
                .where(
                    Bid.id == bid_id,
                )
                .returning(Bid)
            )
            update_bid = await session.execute(update_bid_query)
            await session.commit()
            update_bid = update_bid.scalar_one()

            create_bid_version_query = insert(BidVersion).values(
                name=update_bid.name,
                description=update_bid.description,
                author_type=update_bid.author_type,
                tender_id=update_bid.tender_id,
                status=BidStatusType.Created,
                version=update_bid.version,
                author_id=update_bid.author_id,
                bid_id=update_bid.id,
            )
            await session.execute(create_bid_version_query)
            await session.commit()

            return update_bid

        return bid


@router.patch("/{bid_id}/edit")
async def edit_bid(
    bid_id: uuid.UUID,
    username: str,
    bid_update: BidUpdateSchema,
) -> BidSchema:
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

        get_bid_query = (
            select(Bid)
            .select_from(Bid)
            .join(
                BidResponsible,
                Bid.id == BidResponsible.bid_id,
            )
            .outerjoin(
                OrganizationResponsible,
                BidResponsible.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    Bid.id == bid_id,
                    or_(
                        OrganizationResponsible.user_id == user.id,
                        and_(
                            Bid.author_id == user.id,
                            Bid.author_type == BidAuthorType.User,
                        ),
                    ),
                ),
            )
        )
        bid = await session.execute(get_bid_query)

        try:
            bid = bid.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Такого предложения нет",
            )

        update_values = {}
        for key, value in bid_update:
            if value != "" or value is not None:
                update_values[key] = value

        if update_values:
            update_bid_query = (
                update(Bid)
                .values(
                    **update_values,
                    version=Bid.version + 1,
                )
                .where(
                    Bid.id == bid_id,
                )
                .returning(Bid)
            )
            update_bid = await session.execute(update_bid_query)
            await session.commit()
            update_bid = update_bid.scalar_one()

            create_bid_version_query = insert(BidVersion).values(
                name=update_bid.name,
                description=update_bid.description,
                author_type=update_bid.author_type,
                tender_id=update_bid.tender_id,
                status=BidStatusType.Created,
                version=update_bid.version,
                author_id=update_bid.author_id,
                bid_id=update_bid.id,
            )
            await session.execute(create_bid_version_query)
            await session.commit()

            return update_bid
        return bid


@router.put("/{bid_id}/submit_decision")
async def submit_bid_decision(
    bid_id: uuid.UUID,
    decision: BidDecisionType,
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

        get_bid_query = select(Bid).where(
            Bid.id == bid_id,
            Bid.status == BidStatusType.Published,
        )
        bid = await session.execute(get_bid_query)

        try:
            bid = bid.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого предложения нет",
            )

        get_tender_query = select(Tender).where(Tender.id == bid.tender_id)
        tender = await session.execute(get_tender_query)

        try:
            tender = tender.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого тендера нет",
            )

        if tender.status == TenderStatusType.Closed:
            raise HTTPException(
                status_code=401,
                detail="Данный тендер уже закрыт",
            )

        resonsible_users_query = (
            select(BidResponsible)
            .select_from(BidResponsible)
            .outerjoin(
                OrganizationResponsible,
                BidResponsible.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(BidResponsible.bid_id == bid_id)
        )
        resonsible_users = await session.execute(resonsible_users_query)

        resonsible_users = resonsible_users.scalars().all()
        count_resp_users = len(resonsible_users)

        bid_decision_query = insert(BidDecision).values(
            bid_id=bid_id,
            decision=decision,
            username=username,
        )
        await session.execute(bid_decision_query)
        await session.commit()

        if decision == BidDecisionType.Rejected:
            bid_query = (
                update(Bid)
                .values(
                    status=BidStatusType.Canceled,
                )
                .returning(Bid)
            )

            bid = await session.execute(bid_query)
            await session.commit()

            return bid.scalar_one()

        bid_decisions_query = select(BidDecision).where(BidDecision.bid_id == bid_id)
        bid_decisions = await session.execute(bid_decisions_query)
        bid_decisions = bid_decisions.scalars().all()

        if any(
            decision.decision == BidDecisionType.Rejected for decision in bid_decisions
        ):
            return bid

        quorum_size = min(3, max(count_resp_users, 1))

        if quorum_size <= len(bid_decisions):
            tender_close_query = (
                update(Tender)
                .values(
                    status=TenderStatusType.Closed,
                )
                .where(Tender.id == bid.tender_id)
            )

            await session.execute(tender_close_query)
            await session.commit()
    return bid


@router.put("/{bid_id}/feedback")
async def bid_feedback(
    bid_id: uuid.UUID,
    bid_feedback: str,
    username: str,
) -> BidSchema:
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

        get_bid_query = (
            select(Bid)
            .select_from(Bid)
            .join(
                Tender,
                Bid.tender_id == Tender.id,
            )
            .outerjoin(
                OrganizationResponsible,
                Tender.organization_id == OrganizationResponsible.organization_id,
            )
            .where(
                Bid.id == bid_id,
                OrganizationResponsible.user_id == user.id,
                Bid.status == BidStatusType.Published,
            )
        )

        bid = await session.execute(get_bid_query)

        try:
            bid = bid.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Такого предложения нет",
            )

        insert_bid_review_query = insert(BidReview).values(
            description=bid_feedback,
            bid_id=bid_id,
        )
        await session.execute(insert_bid_review_query)
        await session.commit()

        return bid


@router.put("/{bid_id}/rollback/{version}")
async def bid_rollback(
    bid_id: uuid.UUID,
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

        get_bid_query = (
            select(BidVersion)
            .select_from(BidVersion)
            .join(
                BidResponsible,
                BidVersion.bid_id == BidResponsible.bid_id,
            )
            .outerjoin(
                OrganizationResponsible,
                BidResponsible.organization_id
                == OrganizationResponsible.organization_id,
            )
            .where(
                and_(
                    BidVersion.bid_id == bid_id,
                    or_(
                        OrganizationResponsible.user_id == user.id,
                        and_(
                            BidVersion.author_id == user.id,
                            BidVersion.author_type == BidAuthorType.User,
                        ),
                    ),
                    BidVersion.version == version,
                ),
            )
        )
        bid_version = await session.execute(get_bid_query)

        try:
            bid_version = bid_version.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="Такого предложения нет",
            )

        update_bid_query = (
            update(Bid)
            .values(
                name=bid_version.name,
                description=bid_version.description,
                status=bid_version.status,
                author_type=bid_version.author_type,
                author_id=bid_version.author_id,
                tender_id=bid_version.tender_id,
                version=Bid.version + 1,
            )
            .where(
                Bid.id == bid_id,
            )
            .returning(Bid)
        )
        update_bid = await session.execute(update_bid_query)
        await session.commit()
        update_bid = update_bid.scalar_one()

        create_bid_version_query = insert(BidVersion).values(
            name=update_bid.name,
            description=update_bid.description,
            author_type=update_bid.author_type,
            tender_id=update_bid.tender_id,
            status=BidStatusType.Created,
            version=update_bid.version,
            author_id=update_bid.author_id,
            bid_id=update_bid.id,
        )
        await session.execute(create_bid_version_query)
        await session.commit()

        return update_bid


@router.get("/{tender_id}/reviews")
async def tender_reviews(
    tender_id: uuid.UUID,
    author_username: str,
    requester_username: str,
    limit: int = 5,
    offset: int = 0,
) -> list[BidDecisionSchema]:
    async with async_session_maker() as session:
        requester_user_query = select(User).where(User.username == requester_username)
        requester_user = await session.execute(requester_user_query)
        try:
            requester_user = requester_user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        author_user_query = select(User).where(User.username == author_username)
        author_user = await session.execute(author_user_query)
        try:
            author_user = author_user.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=401,
                detail="Такого пользователя нет",
            )

        get_requester_user_tender_query = (
            select(Tender)
            .select_from(Tender)
            .outerjoin(
                OrganizationResponsible,
                Tender.organization_id == OrganizationResponsible.organization_id,
            )
            .where(
                Tender.id == tender_id,
                OrganizationResponsible.user_id == requester_user.id,
            )
        )
        requester_user_tender = await session.execute(get_requester_user_tender_query)

        try:
            requester_user_tender = requester_user_tender.scalar_one()
        except NoResultFound:
            raise HTTPException(
                status_code=403,
                detail="Нет прав на получение данных",
            )

        bid_reviews_query = (
            select(BidReview)
            .select_from(BidReview)
            .join(
                Bid,
                BidReview.bid_id == Bid.id,
            )
            .where(
                Bid.tender_id == tender_id,
                Bid.author_id == author_user.id,
            )
            .limit(limit)
            .offset(offset)
        )

        bid_reviews = await session.execute(bid_reviews_query)

        return bid_reviews.scalars().all()
