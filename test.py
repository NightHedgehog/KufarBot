import asyncio
from src.handlers.kufar_handler import fetch_kufar_items
from src.data.config import db

users_collection = db["users"]

default_params = {
    "cat": "17010",  # подкатегория 17010 - Мобильные телефоны
    "lang": "ru",               # язык
    "pb": "5",  # количество страниц (не обязательно)
    "prn": "17000",             # категория 17000 - Телефоны и планшеты
    "rgn": "7",                 # регион
    "size": "10",              # количество товаров на странице
    "sort": "lst.d",            # сортировка
}

async def get_user_filters(user_id: int) -> list:
    user_doc = await users_collection.find_one({"_id": user_id})
    if user_doc:
        return user_doc.get("filters", [])
    return []

async def fetch_kufar_items_with_default_params(params: dict) -> list[dict]:
    # Объединяем постоянные параметры с параметрами из фильтров пользователя
    combined_params = {**default_params, **params}

    return await fetch_kufar_items(combined_params)

async def main():
    filters = await get_user_filters(7503108662)
    for filter_data in filters:
        params = filter_data.get("params", {})
        items = await fetch_kufar_items_with_default_params(params)

        for item in items:
            print(f"{item['title']}\n💵 {item['price']} {item['currency']}\n🔗 {item['url']}\n")


asyncio.run(main())
