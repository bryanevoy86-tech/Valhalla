from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DB_URL = "postgresql+asyncpg://USER:PASS@HOST:PORT/DB"
engine = create_async_engine(DB_URL, future=True, pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
