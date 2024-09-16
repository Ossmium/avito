from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from app.config import settings

# DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(settings.POSTGRES_CONN)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
