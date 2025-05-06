from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()


class Base(DeclarativeBase):
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://dump_user:DumpPWD!@localhost/DUMPDB")

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

#async def get_async_session() -> AsyncSession:
#    async with async_session_maker() as session:
#        yield session