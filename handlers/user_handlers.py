import logging
logging.basicConfig(level=logging.INFO)

from aiogram import F, types, Router
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import async_session_maker
from database.dao import DAO

from filters.chat_type import ChatTypeFilter
from keyboard.reply import user_default_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

user_router = Router()
user_router.message.filter(ChatTypeFilter(["private"]))


class UserAskQuestion(StatesGroup):
    anon_choice = State()
    question = State()


WELCOME_TEXT = (
    "Привет, на связи Студенческий совет Финансового факультета!\n"
    "Этот бот, разработанный нами, — твой помощник в университете.\n\n"
    "Сюда ты можешь обратиться с любой проблемой, сохраняя анонимность, задать вопрос или предложить свою инициативу.\n"
    "Также бот содержит всю важную информацию, которая может тебе понадобиться во время обучения. Всё собрано здесь, нужно просто нажать на кнопку!"
)


@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    async with async_session_maker() as session:
        dao = DAO(session)

        await dao.add_user(
            tg_id=message.from_user.id,
            username=message.from_user.username
        )

    await message.answer(text=WELCOME_TEXT, reply_markup=user_default_kb)


# ====== FAQ: отображение для пользователя (без пагинации, одним сообщением) ======
@user_router.message(F.text == "FAQ ❓")
async def show_faq_user(message: types.Message):
    async with async_session_maker() as session:
        dao = DAO(session)
        faqs = await dao.get_all_faq()
        if not faqs:
            await message.answer("FAQ пуст.", reply_markup=user_default_kb)
            return
        text = "<b>FAQ</b>\n\n"
        for idx, faq in enumerate(faqs, 1):
            text += f"<b>{idx}. ❓ {faq.question}</b>\n<blockquote>{faq.answer}</blockquote>\n\n"
        await message.answer(text, parse_mode="HTML")


# ====== О нас: отображение людей с пагинацией и фото ======
def get_person_pagination_kb(current_idx, total):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        InlineKeyboardButton(text="⬅️", callback_data=f"user_person_prev_{current_idx}"),
        InlineKeyboardButton(text="➡️", callback_data=f"user_person_next_{current_idx}")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@user_router.message(F.text == "O нас ℹ️")
async def show_persons_user(message: types.Message):
    async with async_session_maker() as session:
        dao = DAO(session)
        persons = await dao.get_all_persons()
        if not persons:
            await message.answer("Нет информации о людях.", reply_markup=user_default_kb)
            return
        idx = 0
        person = persons[idx]
        kb = get_person_pagination_kb(idx, len(persons))
        text = f"<b>{person.last_name} {person.first_name}</b>\n{person.position or ''}\n☎️ {person.contact or '—'}"
        if getattr(person, 'file_id', None):
            await message.answer_photo(person.file_id, caption=text, reply_markup=kb or user_default_kb, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=kb or user_default_kb)


@user_router.callback_query(F.data.startswith("user_person_prev_"))
async def user_person_prev_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        persons = await dao.get_all_persons()
        if not persons:
            await callback.answer("Нет информации о людях.")
            return
        current_idx = int(callback.data.split('_')[-1])
        prev_idx = max(current_idx - 1, 0)
        person = persons[prev_idx]
        kb = get_person_pagination_kb(prev_idx, len(persons))
        text = f"<b>{person.last_name} {person.first_name}</b>\n{person.position or ''}\n☎️ {person.contact or '—'}"
        if getattr(person, 'file_id', None):
            from aiogram.types import InputMediaPhoto
            await callback.message.edit_media(InputMediaPhoto(media=person.file_id, caption=text, parse_mode="HTML"), reply_markup=kb or user_default_kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb or user_default_kb, parse_mode="HTML")
        await callback.answer()


@user_router.callback_query(F.data.startswith("user_person_next_"))
async def user_person_next_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        persons = await dao.get_all_persons()
        if not persons:
            await callback.answer("Нет информации о людях.")
            return
        current_idx = int(callback.data.split('_')[-1])
        next_idx = min(current_idx + 1, len(persons) - 1)
        person = persons[next_idx]
        kb = get_person_pagination_kb(next_idx, len(persons))
        text = f"<b>{person.last_name} {person.first_name}</b>\n{person.position or ''}\n☎️ {person.contact or '—'}"
        if getattr(person, 'file_id', None):
            from aiogram.types import InputMediaPhoto
            await callback.message.edit_media(InputMediaPhoto(media=person.file_id, caption=text, parse_mode="HTML"), reply_markup=kb or user_default_kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb or user_default_kb, parse_mode="HTML")
        await callback.answer()


# ====== Мероприятия: отображение с пагинацией и фото ======
def get_event_pagination_kb(current_idx, total):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    # Кнопки всегда отображаются, даже если мероприятий одно
    buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"user_event_prev_{current_idx}"))
    buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"user_event_next_{current_idx}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@user_router.message(F.text == "Мероприятия 💼")
async def show_events_user(message: types.Message):
    async with async_session_maker() as session:
        dao = DAO(session)
        events = await dao.get_all_events()
        if not events:
            await message.answer("Нет мероприятий.", reply_markup=user_default_kb)
            return
        idx = 0
        event = events[idx]
        kb = get_event_pagination_kb(idx, len(events))
        caption = f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}"
        if getattr(event, 'file_id', None):
            await message.answer_photo(event.file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(caption, reply_markup=kb, parse_mode="HTML")


@user_router.callback_query(F.data.startswith("user_event_prev_"))
async def user_event_prev_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        events = await dao.get_all_events()
        if not events:
            await callback.answer("Нет мероприятий.")
            return
        current_idx = int(callback.data.split('_')[-1])
        prev_idx = max(current_idx - 1, 0)
        if prev_idx == current_idx:
            await callback.answer("Вы уже на первом мероприятии.")
            return
        event = events[prev_idx]
        kb = get_event_pagination_kb(prev_idx, len(events))
        caption = f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}"
        if getattr(event, 'file_id', None):
            from aiogram.types import InputMediaPhoto
            await callback.message.edit_media(InputMediaPhoto(media=event.file_id, caption=caption, parse_mode="HTML"), reply_markup=kb or user_default_kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb or user_default_kb, parse_mode="HTML")
        await callback.answer()


@user_router.callback_query(F.data.startswith("user_event_next_"))
async def user_event_next_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        events = await dao.get_all_events()
        if not events:
            await callback.answer("Нет мероприятий.")
            return
        current_idx = int(callback.data.split('_')[-1])
        next_idx = min(current_idx + 1, len(events) - 1)
        if next_idx == current_idx:
            await callback.answer("Вы уже на последнем мероприятии.")
            return
        event = events[next_idx]
        kb = get_event_pagination_kb(next_idx, len(events))
        caption = f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}"
        if getattr(event, 'file_id', None):
            from aiogram.types import InputMediaPhoto
            await callback.message.edit_media(InputMediaPhoto(media=event.file_id, caption=caption, parse_mode="HTML"), reply_markup=kb or user_default_kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb or user_default_kb, parse_mode="HTML")
        await callback.answer()


@user_router.message(F.text == "Задать вопрос ✍️")
async def ask_question_start(message: types.Message, state: FSMContext):
    await state.set_state(UserAskQuestion.anon_choice)
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Анонимно"), KeyboardButton(text="Неанонимно")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    await message.answer("Вы хотите задать вопрос анонимно или неанонимно?", reply_markup=kb)


@user_router.message(UserAskQuestion.anon_choice)
async def ask_question_anon_choice(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    if text == "❌ отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=user_default_kb)
        return
    if text not in ["анонимно", "неанонимно"]:
        await message.answer("Пожалуйста, выберите вариант с клавиатуры.", reply_markup=user_default_kb)
        return
    await state.update_data(is_anon=(text == "анонимно"))
    await state.set_state(UserAskQuestion.question)
    await message.answer("Введите ваш вопрос:", reply_markup=None)


@user_router.message(UserAskQuestion.question)
async def ask_question_collect(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "❌ отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=user_default_kb)
        return
    data = await state.get_data()
    is_anon = data.get("is_anon", True)
    question_text = message.text
    username = message.from_user.username
    group_chat_id = -1002698035579
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"answer_{message.from_user.id}")]])
    # Сохраняем вопрос в базу
    async with async_session_maker() as session:
        dao = DAO(session)
        question_obj = await dao.add_question(
            user_id=message.from_user.id,
            username=username,
            question=question_text,
            is_anon=is_anon
        )
    # Отправляем в группу только красивое сообщение, а в базу — только текст вопроса
    group_msg = (
        f"<b>📝 Новый вопрос!</b>\n"
        f"<b>👤 От:</b> <i>{username}</i> {'(анонимно)' if is_anon else ''}\n"
        f"<b>❓ Вопрос:</b>\n<blockquote>{question_text}</blockquote>\n\n"
        f"<i>Для ответа нажмите кнопку ниже 👇</i>"
    )
    import logging
    from aiogram.exceptions import TelegramNetworkError
    try:
        logging.info(f"Отправка вопроса в группу: chat_id={group_chat_id}, user={username}, anon={is_anon}")
        await message.bot.send_message(group_chat_id, group_msg, parse_mode="HTML", reply_markup=kb)
    except TelegramNetworkError as e:
        logging.error(f"TelegramNetworkError при отправке вопроса в группу: {e}")
        await message.answer("❗️ Ошибка сети Telegram. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Ошибка отправки вопроса в группу: {e}")
        await message.answer("❗️ Не удалось отправить вопрос. Сообщите администратору.")
    await state.clear()
    await message.answer("Ваш вопрос отправлен!", reply_markup=user_default_kb)



