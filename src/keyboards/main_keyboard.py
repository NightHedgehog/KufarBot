from enum import Enum

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

class MainKeyboardButtons(Enum):
    MY_FILTERS = "🎯 Мои фильтры"
    ADD_FILTER = "➕ Добавить фильтр"
    RUN_FOLLOWING = "🔄 Запустить отслеживание"

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MainKeyboardButtons.MY_FILTERS.value)],
        [KeyboardButton(text=MainKeyboardButtons.ADD_FILTER.value)],
        [KeyboardButton(text=MainKeyboardButtons.RUN_FOLLOWING.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выбери команду"
)
