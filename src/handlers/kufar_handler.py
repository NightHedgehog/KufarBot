import aiohttp

KUFAR_API = "https://api.kufar.by/search-api/v2/search/rendered-paginated"
default_params = {
    "cat": "17010",  # подкатегория 17010 - Мобильные телефоны
    "lang": "ru",  # язык
    "pb": "5",  # количество страниц (не обязательно)
    "prn": "17000",  # категория 17000 - Телефоны и планшеты
    "rgn": "7",  # регион
    "size": "10",  # количество товаров на странице
    "sort": "lst.d",  # сортировка
}

async def fetch_kufar_items(params: dict) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        combine = {**default_params, **params}
        async with session.get(KUFAR_API, params=combine) as response:
            data = await response.json()

    results = []
    items = data.get("ads", [])

    for item in items:
        ad_id = item.get("ad_id")
        url = item.get("ad_link")
        title = item.get("subject")
        price = item.get("price_byn")
        currency = item.get("currency")

        results.append({
            "id": ad_id,
            "url": url,
            "title": title,
            "price": int(price) / 100,
            "currency": currency,
        })

    return results


# async def fetch_kufar_items_by_filters_by_name(params: dict) -> list[dict]:
#     async with aiohttp.ClientSession() as session:
#         params
#         async with session.get(KUFAR_API, params=params) as response:
#             data = await response.json()
#
#     results = []
#     items = data.get("ads", [])
#
#     for item in items:
#         ad_id = item.get("ad_id")
#         url = item.get("ad_link")
#         title = item.get("subject")
#         price = item.get("price_byn")
#         currency = item.get("currency")
#
#         results.append({
#             "id": ad_id,
#             "url": url,
#             "title": title,
#             "price": int(price) / 100,
#             "currency": currency,
#         })
#
#     return results
