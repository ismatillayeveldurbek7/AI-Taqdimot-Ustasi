from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select
from config import DATABASE_URL, ADMIN_IDS
from models import Base, CoinPackage, Setting, Admin

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create all tables and seed default data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ── Seed default coin packages ─────────────────────────────────────────
        result = await session.execute(select(CoinPackage))
        if not result.scalars().first():
            packages = [
                CoinPackage(coins=10,  price_uzs=10_000),
                CoinPackage(coins=25,  price_uzs=22_000),
                CoinPackage(coins=50,  price_uzs=40_000),
                CoinPackage(coins=100, price_uzs=75_000),
            ]
            session.add_all(packages)

        # ── Seed default settings ──────────────────────────────────────────────
        defaults = {
            "card_number": "8600 1234 5678 9012",
            "card_owner": "Bot Admin",
            "support_username": "@admin",
            "about_text": "Bu bot AI yordamida professional taqdimotlar yaratadi.",
        }
        for key, val in defaults.items():
            exists = await session.execute(select(Setting).where(Setting.key == key))
            if not exists.scalars().first():
                session.add(Setting(key=key, value=val))

        # ── Seed admins from config ────────────────────────────────────────────
        for tg_id in ADMIN_IDS:
            exists = await session.execute(select(Admin).where(Admin.telegram_id == tg_id))
            if not exists.scalars().first():
                session.add(Admin(telegram_id=tg_id))

        await session.commit()


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    result = await session.execute(select(Setting).where(Setting.key == key))
    obj = result.scalars().first()
    return obj.value if obj else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    result = await session.execute(select(Setting).where(Setting.key == key))
    obj = result.scalars().first()
    if obj:
        obj.value = value
    else:
        session.add(Setting(key=key, value=value))
    await session.commit()
