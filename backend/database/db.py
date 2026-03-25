"""
Database initialisation — PostgreSQL (async via SQLAlchemy) + MongoDB + Redis
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis as AsyncRedis
from config import settings


# ── SQLAlchemy (PostgreSQL) ──────────────────────────────────────────────────
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=10)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── MongoDB ──────────────────────────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = mongo_client["safetrail"]
incidents_collection = mongo_db["incidents"]
events_collection    = mongo_db["events"]


# ── Redis ────────────────────────────────────────────────────────────────────
redis_client = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)


# ── Init ─────────────────────────────────────────────────────────────────────
async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
