from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

search_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛑 Остановить отслеживание")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выбери команду"
)
