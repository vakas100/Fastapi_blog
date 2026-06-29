from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker,create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"  # +aiosqlite is used to tell which async driver is used

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    with AsyncSessionLocal() as session:
        yield session