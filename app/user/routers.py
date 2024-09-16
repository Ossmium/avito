from fastapi import APIRouter
from sqlalchemy import insert, select

from app.user.models import User
from app.user.schemas import UserCreateSchema, UserSchema
from app.database import async_session_maker

router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.get("")
async def users_list() -> list[UserSchema]:
    async with async_session_maker() as session:
        query = select(User)
        result = await session.execute(query)
        return result.scalars().all()


@router.post("/new")
async def create_user(user: UserCreateSchema):
    async with async_session_maker() as session:
        query = insert(User).values(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        await session.execute(query)
        await session.commit()
