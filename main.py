import asyncio
import logging
from config.settings import settings

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.handlers import main_hanlder, search_handler, filter_handler


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode='HTML')
    )

    dp = Dispatcher()
    dp.include_routers(main_hanlder.router, filter_handler.router, search_handler.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
