import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
load_dotenv()

from handlers.user_handlers import user_router
from handlers.admin_handlers import admin_router
from database.engine import async_session_maker
from database.dao import DAO

bot = Bot(token=os.getenv('TOKEN'))
bot.my_admins_list = [922109605, 297648299, 8154592734, 816800090, 778706249]
# bot.my_admins_list = [297648299, 8154592734, 816800090, 778706249]

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(admin_router)
dp.include_router(user_router)


async def main():
    print("Работает")
   
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())