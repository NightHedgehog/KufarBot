from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.database import connection

models_collection = connection["models"]


async def generate_model_keyboard(columns: int = 2):
    cursor = models_collection.find({})
    buttons_flat = []

    async for model in cursor:
        title = model["title"]
        phm = model["phm"]
        callback_data = f"phm={title}={phm}"
        buttons_flat.append(InlineKeyboardButton(text=title, callback_data=callback_data))

    keyboard = [
        buttons_flat[i:i + columns]
        for i in range(0, len(buttons_flat), columns)
    ]

    keyboard.append([InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel_add_filter")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


price_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="до 1 000 BYN", callback_data="prc=r:0,100000")],
        [InlineKeyboardButton(text="до 1 500 BYN", callback_data="prc=r:0,150000")],
        [InlineKeyboardButton(text="до 2 000 BYN", callback_data="prc=r:0,200000")],
        [InlineKeyboardButton(text="до 2 500 BYN", callback_data="prc=r:0,250000")],
        [InlineKeyboardButton(text="до 3 000 BYN", callback_data="prc=r:0,300000")],
        [InlineKeyboardButton(text="до 3 500 BYN", callback_data="prc=r:0,350000")],
        [InlineKeyboardButton(text="до 4 000 BYN", callback_data="prc=r:0,400000")],
        [InlineKeyboardButton(text="до 10 000 BYN", callback_data="prc=r:0,1000000")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_models")]
    ]
)
