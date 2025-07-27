from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.database import connection
from src.keyboards.main_keyboard import main_menu

router = Router()
users_collection = connection["users"]


# 📥 /start
@router.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        await users_collection.insert_one({"_id": user_id, "filters": []})
        await message.answer(
            "👋 Привет! Я бот для отслеживания товаров на Kufar.\nТы можешь задать фильтр и я буду присылать тебе"
            "новые объявления.\n\n"
            "Выбери действие ниже 👇",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "👋 Привет! Я помогу тебе отслеживать объявления на Kufar.\n\n"
            "Выбери действие ниже 👇",
            reply_markup=main_menu
        )
