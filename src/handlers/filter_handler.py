from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F, Router

from src.keyboards.filter_keyboard import generate_model_keyboard, price_menu
from src.keyboards.main_keyboard import main_menu, MainKeyboardButtons

from src.database.connection import connection

router = Router()
users_collection = connection["users"]


# 👉 Машина состояний (FSM)
class FilterState(StatesGroup):
    choosing_model = State()
    choosing_price = State()
    selecting_for_deletion = State()

########################################################################################################################

# 📥 Команда ➕ Добавить фильтр
@router.message(F.text == MainKeyboardButtons.ADD_FILTER.value)
async def add_filter_command(message: Message, state: FSMContext):
    iphone_menu = await generate_model_keyboard()
    await message.answer(
        "📝 Выберите модель устройства",
        reply_markup=iphone_menu
    )
    await state.set_state(FilterState.choosing_model)


# 💬 Пользователь отправил модель
@router.callback_query(FilterState.choosing_model, F.data.startswith("phm="))
async def handle_model_choice(callback: CallbackQuery, state: FSMContext):
    phm_title = callback.data.split("=")[1]
    phm_value = callback.data.split("=")[2]
    await state.update_data(title=phm_title, phm=phm_value)

    await callback.message.edit_text(
        "💰 Теперь выбери диапазон цены:",
        reply_markup=price_menu)
    await state.set_state(FilterState.choosing_price)
    await callback.answer()


# 💬 Пользователь отправил стоимость
@router.callback_query(FilterState.choosing_price, F.data.startswith("prc="))
async def handle_price_choice(callback: CallbackQuery, state: FSMContext):
    prc_value = callback.data.split("=")[1]
    data = await state.get_data()
    phm = data.get("phm")
    title = data.get("title")

    # Собираем фильтр
    filter_entry = {
        "title": title,
        "params": {
            "phm": phm,
            "prc": prc_value
        }
    }

    # Сохраняем в MongoDB
    await users_collection.update_one(
        {"_id": callback.from_user.id},
        {"$push": {"filters": filter_entry}},
        upsert=True
    )

    await callback.message.edit_text("✅ Фильтр успешно добавлен!")
    await callback.message.answer("🔽 Меню", reply_markup=main_menu)
    await state.clear()
    await callback.answer()

# 💬 Пользователь нажал отмена
@router.callback_query(FilterState.choosing_model, F.data == "cancel_add_filter")
async def back_to_models(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("🔽 Меню", reply_markup=main_menu)
    await state.clear()
    await callback.answer()

# 💬 Пользователь нажал назад
@router.callback_query(FilterState.choosing_price, F.data == "back_to_models")
async def back_to_models(callback: CallbackQuery, state: FSMContext):
    iphone_menu = await generate_model_keyboard()
    await callback.message.edit_text(
        "📝 Выберите модель устройства:",
        reply_markup=iphone_menu
    )
    await state.set_state(FilterState.choosing_model)
    await callback.answer()

########################################################################################################################

async def render_filter_selection_keyboard(user_id: int, selected_indexes: list[int]) -> InlineKeyboardMarkup:
    user = await users_collection.find_one({"_id": user_id})
    filters = user.get("filters", [])
    keyboard = []

    for i, f in enumerate(filters):
        title = f.get("title", "Без названия")
        prc = int(f["params"]["prc"].split(",")[1]) / 100
        checked = "✅" if i in selected_indexes else "☐"
        text = f"{checked} {title} — до {int(prc)} BYN"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"toggle_select:{i}")])

    # Кнопка удаления, если есть выбранные
    if selected_indexes:
        keyboard.append([
            InlineKeyboardButton(text="❌ Удалить выбранные", callback_data="confirm_deletion")
        ])

    # Назад
    keyboard.append([
        InlineKeyboardButton(text="✅ Вернуться в меню", callback_data="back_to_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# 📥 Команда 🎯 Мои фильтры
@router.message(F.text == "🎯 Мои фильтры")
async def show_filter_selection(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await users_collection.find_one({"_id": user_id})

    if not user or not user.get("filters"):
        await message.answer(
            "🔍 У тебя пока нет сохранённых фильтров.",
            reply_markup=main_menu
        )
        return

    await state.set_state(FilterState.selecting_for_deletion)
    await state.update_data(selected=[])
    markup = await render_filter_selection_keyboard(message.from_user.id, [])
    await message.answer("📄 Проверьте фильтры", reply_markup=markup)


@router.callback_query(FilterState.selecting_for_deletion, F.data.startswith("toggle_select:"))
async def toggle_filter(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = data.get("selected", [])

    if index in selected:
        selected.remove(index)
    else:
        selected.append(index)

    await state.update_data(selected=selected)

    # Обновим клавиатуру
    markup = await render_filter_selection_keyboard(callback.from_user.id, selected)
    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()


@router.callback_query(FilterState.selecting_for_deletion, F.data == "confirm_deletion")
async def confirm_deletion(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])

    user_id = callback.from_user.id
    user = await users_collection.find_one({"_id": user_id})
    filters = user.get("filters", [])

    # Удалим выбранные
    filters = [f for i, f in enumerate(filters) if i not in selected]

    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"filters": filters}}
    )

    # Обновляем состояние и отрисовываем клавиатуру
    await state.update_data(selected=[])  # очищаем выбор
    updated_keyboard = await render_filter_selection_keyboard(user_id, [])

    await callback.message.edit_text(
        "✅ Выбранные фильтры удалены\n📄 Обновлённый список фильтров:",
        reply_markup=updated_keyboard
    )
    await callback.answer()

# @router.callback_query(FilterState.selecting_for_deletion, F.data == "back_to_main"):
# 💬 Пользователь нажал отмена
@router.callback_query(FilterState.selecting_for_deletion, F.data == "back_to_main")
async def back_to_models(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("🔽 Меню", reply_markup=main_menu)
    await state.clear()
    await callback.answer()
