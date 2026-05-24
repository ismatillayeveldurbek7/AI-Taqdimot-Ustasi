import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import admin, payment, presentation, user
from utils.logger import logger


async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in .env file!")

    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: admin va payment avval, user eng oxirida
    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(presentation.router)
    dp.include_router(user.router)

    logger.info("Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
