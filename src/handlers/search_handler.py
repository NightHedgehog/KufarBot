import asyncio

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import F, Router
from aiogram import Bot

from src.database.connection import connection
from src.keyboards.search_keyboard import search_keyboard
from src.keyboards.main_keyboard import main_menu
from src.handlers.kufar_handler import fetch_kufar_items


class TrackingState(StatesGroup):
    active = State()


router = Router()
tracking_list_collection = connection["tracking_list"]
users_collection = connection["users"]

user_tracking_tasks = {}


async def get_user_filters(user_id: int) -> list:
    user_doc = await users_collection.find_one({"_id": user_id})
    if user_doc:
        return user_doc.get("filters", [])
    return []


async def get_seen_items(user_id: int) -> list[str]:
    user = await users_collection.find_one({"_id": user_id})
    return user.get("seen_ids", []) if user else []


async def save_seen_items(user_id: int, item_ids: list[str]):
    await users_collection.update_one(
        {"_id": user_id},
        {"$addToSet": {"seen_ids": {"$each": item_ids}}},
        upsert=True
    )


default_params = {
    "cat": "17010",  # подкатегория 17010 - Мобильные телефоны
    "lang": "ru",  # язык
    "pb": "5",  # количество страниц (не обязательно)
    "prn": "17000",  # категория 17000 - Телефоны и планшеты
    "rgn": "7",  # регион
    "size": "10",  # количество товаров на странице
    "sort": "lst.d",  # сортировка
}


async def fetch_kufar_items_with_default_params(params: dict) -> list[dict]:
    combined_params = {**default_params, **params}

    return await fetch_kufar_items(combined_params)


async def check_new_products(user_id: int, filters: list[dict]) -> list[dict]:
    all_new_items = []
    seen_ids = await get_seen_items(user_id)

    for filter_data in filters:
        params = filter_data.get("params", {})
        found_items = await fetch_kufar_items_with_default_params(params)

        new_items = [item for item in found_items if item["id"] not in seen_ids]

        if new_items:
            await save_seen_items(user_id, [item["id"] for item in new_items])
            all_new_items.extend(new_items)

    return all_new_items


def format_new_items(items: list[dict]) -> str:
    lines = []
    for item in items:
        lines.append(f"<b>{item['title']}</b>\n💵 {item['price']} {item['currency']}\n🔗 {item['url']}\n")
    return "\n".join(lines)


async def tracking_worker(bot: Bot, user_id):
    while True:
        filters = await get_user_filters(user_id)
        if not filters:
            await bot.send_message(user_id, "❗️У вас нет фильтров. Отслеживание остановлено.")
            user_tracking_tasks.pop(user_id, None)
            break

        new_items = await check_new_products(user_id, filters)
        if new_items:
            text = format_new_items(new_items)
            await bot.send_message(user_id, f"🆕 Найдено: \n{text}")

        await asyncio.sleep(300)


#####################################################################################################################
# Получить всех отслеживающих
async def get_all_tracking_users() -> list[int]:
    cursor = tracking_list_collection.find({})
    users = await cursor.to_list(length=None)
    return [user["user_id"] for user in users]


# Добавить пользователя
async def add_tracking_user(user_id: int):
    await tracking_list_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id}},
        upsert=True
    )


# 🔄 Запустить отслеживание
@router.message(F.text == "🔄 Запустить отслеживание")
async def start_tracking(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_ids = await get_all_tracking_users()

    if user_id in user_ids:
        await message.answer("🔁 Отслеживание уже запущено.", reply_markup=search_keyboard)
        return

    filters = await get_user_filters(user_id)
    if not filters:
        await message.answer("❗️У вас нет фильтров для отслеживания.", reply_markup=main_menu)
        return

    await add_tracking_user(user_id)
    await state.set_state(TrackingState.active)

    task = asyncio.create_task(tracking_worker(message.bot, user_id))
    user_tracking_tasks[user_id] = task

    await message.answer("🟢 Отслеживание запущено.", reply_markup=search_keyboard)


#######################################################################################################################
# Удалить пользователя
async def remove_tracking_user(user_id: int):
    await tracking_list_collection.delete_one({"user_id": user_id})


# 🛑 Остановить отслеживание
@router.message(F.text == "🛑 Остановить отслеживание")
async def stop_tracking(message: Message, state: FSMContext):
    user_id = message.from_user.id

    await remove_tracking_user(user_id)
    await state.clear()

    task = user_tracking_tasks.pop(user_id, None)
    if task:
        task.cancel()

    await message.answer("⛔️ Отслеживание остановлено.", reply_markup=main_menu)
