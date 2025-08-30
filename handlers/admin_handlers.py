import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from sqlalchemy import update

from filters.chat_type import ChatTypeFilter, IsAdmin
from database.dao import DAO
from keyboard.reply import admin_edit_kb, mailing_kb, gaz_kb
from states_fsm import (AdminAddFAQ,
                        AdminAddEvent,
                        AdminAddPerson,
                        AdminEditEvent,
                        AdminEditFAQ,
                        AdminEditPerson,
                        AdminMailing,
                        AdminDeleteFAQ)  # Добавьте AdminDeleteFAQ в states_fsm.py

from keyboard.inline import get_admin_pagination_kb, faq_admin_kb
from database.engine import async_session_maker
from aiogram.fsm.state import State, StatesGroup


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


WELCOME_TEXT = (
    "Что сегодня делаем, Босс?"
)

ADMINS_LIST = [922109605, 297648299, 8154592734, 816800090, 778706249]


@admin_router.message(CommandStart())
async def user_start_cmd(message: types.Message):
    await message.answer(
        WELCOME_TEXT,
        reply_markup=admin_edit_kb
    )


# ====== РАССЫЛКА СООБЩЕНИЙ ======
@admin_router.message(F.text == "📥 Рассылка")
async def start_mailing(message: types.Message, state: FSMContext):
    await state.set_state(AdminMailing.content_type)
    await message.answer("Отправьте сообщение для рассылки (текст, фото, видео, голос, кружок и т.д.)")


@admin_router.message(AdminMailing.content_type)
async def collect_content(message: types.Message, state: FSMContext):
    content = {}
    if message.text:
        content['type'] = 'text'
        content['data'] = message.text
    elif message.photo:
        content['type'] = 'photo'
        content['data'] = message.photo[-1].file_id
        content['caption'] = message.caption
    elif message.video:
        content['type'] = 'video'
        content['data'] = message.video.file_id
        content['caption'] = message.caption
    elif message.voice:
        content['type'] = 'voice'
        content['data'] = message.voice.file_id
    elif message.video_note:
        content['type'] = 'video_note'
        content['data'] = message.video_note.file_id
    else:
        await message.answer("Тип сообщения не поддерживается. Попробуйте ещё раз.")
        return
    await state.update_data(content=content)
    await state.set_state(AdminMailing.confirm_type)
    await message.answer("Выберите тип рассылки:", reply_markup=mailing_kb)


@admin_router.message(AdminMailing.confirm_type)
async def choose_mailing_type(message: types.Message, state: FSMContext):
    data = await state.get_data()
    content = data.get('content')
    ADMINS_LIST = [922109605, 297648299, 8154592734, 816800090, 778706249]  
    if message.text == "Тестовая рассылка":
        sent = 0
        for admin_id in ADMINS_LIST:
            try:
                await send_content(message.bot, admin_id, content)
                sent += 1
            except Exception:
                pass
        await state.clear()
        await return_admin_keyboard(message, f"Тестовая рассылка отправлена {sent} админам.")
    elif message.text == "Рассылка для всех":
        await state.set_state(AdminMailing.confirm_all)
        await message.answer("Точно прям всем-всем рассылаем?", reply_markup=gaz_kb)
    else:
        await message.answer("Выберите вариант рассылки с клавиатуры.")


@admin_router.message(AdminMailing.confirm_all)
async def confirm_and_send_all(message: types.Message, state: FSMContext):
    if message.text != "Полетели 🚀":
        await state.clear()
        await return_admin_keyboard(message, "Рассылка отменена.")
        return
    data = await state.get_data()
    content = data.get('content')
    from database.engine import async_session_maker
    from database.dao import DAO
    async with async_session_maker() as session:
        dao = DAO(session)
        users = await dao.session.execute(dao.session.query(dao.session.bind.classes.Users.tg_id))
        user_ids = [row[0] for row in users.fetchall()]
    sent = 0
    for user_id in user_ids:
        try:
            await send_content(message.bot, user_id, content)
            sent += 1
        except Exception:
            pass
    await state.clear()
    await return_admin_keyboard(message, f"Рассылка завершена! Отправлено {sent} из {len(user_ids)} пользователей.")


async def send_content(bot, user_id, content):
    if content['type'] == 'text':
        await bot.send_message(user_id, content['data'])
    elif content['type'] == 'photo':
        await bot.send_photo(user_id, content['data'], caption=content.get('caption'))
    elif content['type'] == 'video':
        await bot.send_video(user_id, content['data'], caption=content.get('caption'))
    elif content['type'] == 'voice':
        await bot.send_voice(user_id, content['data'])
    elif content['type'] == 'video_note':
        await bot.send_video_note(user_id, content['data'])


# ====== Мероприятия: отображение с пагинацией ======
@admin_router.message(F.text == "✏️ Мероприятия")
async def show_events(message: types.Message):

    async with async_session_maker() as session:
        dao = DAO(session)
        events = await dao.get_all_events()
        if not events:
            await message.answer("Нет мероприятий. Нажмите ➕ чтобы добавить.", reply_markup=get_admin_pagination_kb('event'))
            return
        event = events[0]
        caption = f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}"
        if getattr(event, 'file_id', None):
            await message.answer_photo(
                event.file_id,
                caption=caption,
                reply_markup=get_admin_pagination_kb('event', event.id),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                caption,
                reply_markup=get_admin_pagination_kb('event', event.id),
                parse_mode="HTML"
            )


# ====== Пагинация мероприятий ======
@admin_router.callback_query(F.data.startswith("event_prev"))
async def event_prev_page(callback: types.CallbackQuery, state: FSMContext):

    async with async_session_maker() as session:
        dao = DAO(session)
        events = await dao.get_all_events()
        if not events:
            await callback.answer("Нет мероприятий.")
            return
        current_id = None

        if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
            for row in callback.message.reply_markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data and btn.callback_data.startswith("event_edit_"):
                        try:
                            current_id = int(btn.callback_data.split('_')[-1])
                        except:
                            pass
        idx = next((i for i, e in enumerate(events) if e.id == current_id), 0)
        prev_idx = (idx - 1) % len(events)
        event = events[prev_idx]
        from aiogram.types import InputMediaPhoto
        try:
            if getattr(event, 'file_id', None):
                caption = f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}"
                await callback.message.edit_media(
                    InputMediaPhoto(media=event.file_id, caption=caption, parse_mode="HTML"),
                    reply_markup=get_admin_pagination_kb('event', event.id)
                )
            else:
                await callback.message.edit_text(
                    f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}",
                    reply_markup=get_admin_pagination_kb('event', event.id),
                    parse_mode="HTML"
                )
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
        await callback.answer()


@admin_router.callback_query(F.data.startswith("event_next"))
async def event_next_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        events = await dao.get_all_events()
        if not events:
            await callback.answer("Нет мероприятий.")
            return
        current_id = None
        if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
            for row in callback.message.reply_markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data and btn.callback_data.startswith("event_edit_"):
                        try:
                            current_id = int(btn.callback_data.split('_')[-1])
                        except Exception:
                            pass
        idx = next((i for i, e in enumerate(events) if e.id == current_id), 0)
        next_idx = (idx + 1) % len(events)
        event = events[next_idx]
        from aiogram.types import InputMediaPhoto
        try:
            if getattr(event, 'file_id', None):
                caption = f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}"
                await callback.message.edit_media(
                    InputMediaPhoto(media=event.file_id, caption=caption, parse_mode="HTML"),
                    reply_markup=get_admin_pagination_kb('event', event.id)
                )
            else:
                await callback.message.edit_text(
                    f"<b>{event.title}</b>\n{event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n📍 {event.location}",
                    reply_markup=get_admin_pagination_kb('event', event.id),
                    parse_mode="HTML"
                )
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
        await callback.answer()


# ====== Добавление мероприятия ======
@admin_router.callback_query(F.data == "event_add")
async def event_add_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminAddEvent.title)
    await callback.message.answer("Введите название мероприятия:")
    await callback.answer()


@admin_router.message(AdminAddEvent.title)
async def event_add_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminAddEvent.description)
    await message.answer("Введите описание мероприятия:")


@admin_router.message(AdminAddEvent.description)
async def event_add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminAddEvent.date)
    await message.answer("Введите дату и время (например, 27.08.2025 18:00):")


@admin_router.message(AdminAddEvent.date)
async def event_add_date(message: types.Message, state: FSMContext):
    from datetime import datetime
    try:
        date = datetime.strptime(message.text, '%d.%m.%Y %H:%M')
    except ValueError:
        await message.answer("Некорректный формат даты! Введите в формате: 27.08.2025 18:00")
        return
    await state.update_data(date=date)
    await state.set_state(AdminAddEvent.location)
    await message.answer("Введите место проведения:")


@admin_router.message(AdminAddEvent.location)
async def event_add_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(AdminAddEvent.file_id)
    await message.answer("Отправьте файл/фото мероприятия или напишите 'Пропустить', если не требуется.")


def return_admin_keyboard(message, text):
    from keyboard.reply import admin_edit_kb
    return message.answer(text, reply_markup=admin_edit_kb)


@admin_router.message(AdminAddEvent.file_id)
async def event_add_file(message: types.Message, state: FSMContext):
    # Обработка отмены
    if message.text and message.text.strip().lower() in ["отмена", "назад"]:
        await state.clear()
        await message.answer("Добавление мероприятия отменено.", reply_markup=admin_edit_kb)
        return
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    await state.update_data(file_id=file_id)
    event_data = await state.get_data()
    async with async_session_maker() as session:
        dao = DAO(session)
        event_data['created_by'] = message.from_user.id
        await dao.add_event(**event_data)
    await state.clear()
    await message.answer("Мероприятие добавлено! 🎉", reply_markup=admin_edit_kb)
@admin_router.message(F.text.regexp(r"^(Отмена|Назад)$"))
async def fsm_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=admin_edit_kb)


@admin_router.message(AdminEditEvent.title)
async def event_edit_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminEditEvent.description)
    await message.answer("Введите новое описание:")


@admin_router.message(AdminEditEvent.description)
async def event_edit_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminEditEvent.date)
    await message.answer("Введите новую дату и время:")


@admin_router.message(AdminEditEvent.date)
async def event_edit_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(AdminEditEvent.location)
    await message.answer("Введите новое место:")


@admin_router.message(AdminEditEvent.location)
async def event_edit_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(AdminEditEvent.file_id)
    await message.answer("Отправьте новый файл/фото (или пропустите):")


@admin_router.message(AdminEditEvent.file_id)
async def event_edit_file(message: types.Message, state: FSMContext):
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    await state.update_data(file_id=file_id)
    await state.set_state(AdminEditEvent.created_by)
    await message.answer("Введите новый user_id (или пропустите):")


@admin_router.message(AdminEditEvent.created_by)
async def event_edit_created_by(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    update_data = {k: v for k, v in data.items() if k != 'event_id'}

    async with async_session_maker() as session:
        await session.execute(
            update(session.bind.classes.Event)
            .where(session.bind.classes.Event.id == event_id)
            .values(**update_data)
        )
        await session.commit()
    await message.answer("Мероприятие обновлено! ✏️")
    await state.clear()


# ====== Удаление мероприятия ======
@admin_router.callback_query(F.data.startswith("event_delete_"))
async def event_delete(callback: types.CallbackQuery):

    async with async_session_maker() as session:
        dao = DAO(session)
        event_id = int(callback.data.split('_')[-1])
        await dao.delete_event(event_id)
        try:
            await callback.message.edit_text("Мероприятие удалено! 🗑️")
        except Exception as e:
            if "there is no text in the message to edit" in str(e):
                await callback.message.delete()
                await callback.message.answer("Мероприятие удалено! 🗑️")
            else:
                raise
        await callback.answer()


# ====== Люди: отображение с пагинацией ======
@admin_router.message(F.text == "✏️ Люди")
async def show_persons(message: types.Message):

    async with async_session_maker() as session:
        dao = DAO(session)
        persons = await dao.get_all_persons()
        if not persons:
            await message.answer("Нет людей. Нажмите ➕ чтобы добавить.", reply_markup=get_admin_pagination_kb('person'))
            return
        person = persons[0]
        caption = f"<b>{person.last_name} {person.first_name}</b>\n{person.position or ''}\n☎️ {person.contact or '—'}"
        if person.file_id:
            await message.answer_photo(person.file_id, caption=caption, reply_markup=get_admin_pagination_kb('person', person.id), parse_mode="HTML")
        else:
            await message.answer(caption, reply_markup=get_admin_pagination_kb('person', person.id), parse_mode="HTML")


# ====== Пагинация людей ======
@admin_router.callback_query(F.data.startswith("person_prev"))
async def person_prev_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        persons = await dao.get_all_persons()
        if not persons:
            await callback.answer("Нет людей.")
            return
        current_id = None
        if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
            for row in callback.message.reply_markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data and btn.callback_data.startswith("person_edit_"):
                        try:
                            current_id = int(btn.callback_data.split('_')[-1])
                        except Exception:
                            pass
        idx = next((i for i, p in enumerate(persons) if p.id == current_id), 0)
        prev_idx = (idx - 1) % len(persons)
        person = persons[prev_idx]
        caption = f"<b>{person.last_name} {person.first_name}</b>\n{person.position or ''}\n☎️ {person.contact or '—'}"
        if person.file_id:
            from aiogram.types import InputMediaPhoto
            await callback.message.edit_media(InputMediaPhoto(media=person.file_id, caption=caption, parse_mode="HTML"), reply_markup=get_admin_pagination_kb('person', person.id))
        else:
            await callback.message.edit_text(caption, reply_markup=get_admin_pagination_kb('person', person.id), parse_mode="HTML")
        await callback.answer()


@admin_router.callback_query(F.data.startswith("person_next"))
async def person_next_page(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        persons = await dao.get_all_persons()
        if not persons:
            await callback.answer("Нет людей.")
            return
        current_id = None
        if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
            for row in callback.message.reply_markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data and btn.callback_data.startswith("person_edit_"):
                        try:
                            current_id = int(btn.callback_data.split('_')[-1])
                        except Exception:
                            pass
        idx = next((i for i, p in enumerate(persons) if p.id == current_id), 0)
        next_idx = (idx + 1) % len(persons)
        person = persons[next_idx]
        caption = f"<b>{person.last_name} {person.first_name}</b>\n{person.position or ''}\n☎️ {person.contact or '—'}"
        if person.file_id:
            from aiogram.types import InputMediaPhoto
            await callback.message.edit_media(InputMediaPhoto(media=person.file_id, caption=caption, parse_mode="HTML"), reply_markup=get_admin_pagination_kb('person', person.id))
        else:
            await callback.message.edit_text(caption, reply_markup=get_admin_pagination_kb('person', person.id), parse_mode="HTML")
        await callback.answer()


# ====== Добавление человека ======
@admin_router.callback_query(F.data == "person_add")
async def person_add_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminAddPerson.last_name)
    await callback.message.answer("Введите фамилию человека:")
    await callback.answer()


@admin_router.message(AdminAddPerson.last_name)
async def person_add_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(AdminAddPerson.first_name)
    await message.answer("Введите имя человека:")


@admin_router.message(AdminAddPerson.first_name)
async def person_add_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(AdminAddPerson.position)
    await message.answer("Введите должность (или пропустите):")


@admin_router.message(AdminAddPerson.position)
async def person_add_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text)
    await state.set_state(AdminAddPerson.contact)
    await message.answer("Введите контактные данные (или пропустите):")


@admin_router.message(AdminAddPerson.contact)
async def person_add_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(AdminAddPerson.file_id)
    await message.answer("Отправьте файл или фото человека (или пропустите):")


@admin_router.message(AdminAddPerson.file_id)
async def person_add_file(message: types.Message, state: FSMContext):
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    await state.update_data(file_id=file_id)
    person_data = await state.get_data()

    async with async_session_maker() as session:
        dao = DAO(session)
        await dao.add_person(**person_data)
    await message.answer("Человек добавлен! 👤")
    await state.clear()


# ====== Редактирование человека ======
@admin_router.callback_query(F.data.startswith("person_edit_"))
async def person_edit_start(callback: types.CallbackQuery, state: FSMContext):

    async with async_session_maker() as session:
        dao = DAO(session)
        person_id = int(callback.data.split('_')[-1])
        person = await dao.get_person(person_id)
        if not person:
            await callback.answer("Человек не найден")
            return
        await state.update_data(person_id=person_id)
        await state.set_state(AdminEditPerson.last_name)
        await callback.message.answer(f"Редактирование: текущая фамилия — {person.last_name}\nВведите новую фамилию:")
        await callback.answer()


@admin_router.message(AdminEditPerson.last_name)
async def person_edit_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(AdminEditPerson.first_name)
    await message.answer("Введите новое имя:")


@admin_router.message(AdminEditPerson.first_name)
async def person_edit_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(AdminEditPerson.position)
    await message.answer("Введите новую должность (или пропустите):")


@admin_router.message(AdminEditPerson.position)
async def person_edit_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text)
    await state.set_state(AdminEditPerson.contact)
    await message.answer("Введите новые контактные данные (или пропустите):")


@admin_router.message(AdminEditPerson.contact)
async def person_edit_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(AdminEditPerson.file_id)
    await message.answer("Отправьте новый файл/фото (или пропустите):")


@admin_router.message(AdminEditPerson.file_id)
async def person_edit_file(message: types.Message, state: FSMContext):
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    await state.update_data(file_id=file_id)
    data = await state.get_data()
    person_id = data.get('person_id')
    update_data = {k: v for k, v in data.items() if k != 'person_id'}

    async with async_session_maker() as session:
        dao = DAO(session)
        # await dao.update_person(person_id, **update_data)
    await message.answer("Данные человека обновлены! ✏️")
    await state.clear()


# ====== Удаление человека ======
@admin_router.callback_query(F.data.startswith("person_delete_"))
async def person_delete(callback: types.CallbackQuery):

    async with async_session_maker() as session:
        dao = DAO(session)
        person_id = int(callback.data.split('_')[-1])
        await dao.delete_person(person_id)
        await callback.message.edit_text("Человек удалён! 🗑️")
        await callback.answer()


# ====== FAQ: отображение всех вопросов одним сообщением ======
@admin_router.message(F.text == "✏️ FAQ")
async def show_faq_admin(message: types.Message):
    async with async_session_maker() as session:
        dao = DAO(session)
        faqs = await dao.get_all_faq()
        if not faqs:
            await message.answer("FAQ пуст. Нажмите ➕ чтобы добавить.", reply_markup=faq_admin_kb)
            return
        text = "<b>FAQ</b>\n\n"
        for idx, faq in enumerate(faqs, 1):
            text += f"<b>{idx}. ❓ {faq.question}</b>\n<blockquote>{faq.answer}</blockquote>\n\n"
        text += "<i>Выберите действие:</i>"
        await message.answer(text, parse_mode="HTML", reply_markup=faq_admin_kb)

# ====== FAQ: отображение для юзера ======
@admin_router.message(F.text == "FAQ ❓")
async def show_faq_user(message: types.Message):
    async with async_session_maker() as session:
        dao = DAO(session)
        faqs = await dao.get_all_faq()
        if not faqs:
            await message.answer("FAQ пуст.")
            return
        faq = faqs[0]
        text = f"<b>{faq.question}</b>\n<blockquote>{faq.answer}</blockquote>"
        await message.answer(text, parse_mode="HTML", reply_markup=None)

# ====== FAQ: добавление вопроса ======
@admin_router.callback_query(F.data == "faq_add")
async def faq_add_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminAddFAQ.question)
    await callback.message.answer("Введите вопрос FAQ:")
    await callback.answer()

@admin_router.message(AdminAddFAQ.question)
async def faq_add_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(AdminAddFAQ.answer)
    await message.answer("Введите ответ на вопрос:")

# ====== FAQ: добавление ответа ======
@admin_router.message(AdminAddFAQ.answer)
async def faq_add_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question = data.get("question")
    answer = message.text
    async with async_session_maker() as session:
        dao = DAO(session)
        await dao.add_faq(question, answer)
    await state.clear()
    await message.answer("FAQ добавлен!", reply_markup=admin_edit_kb)

# ====== FAQ: редактирование (новая логика с выбором номера) ======
@admin_router.callback_query(F.data == "faq_edit")
async def faq_edit_start(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        faqs = await dao.get_all_faq()
        if not faqs:
            await callback.answer("FAQ пуст. Ничего редактировать.")
            return
        text = "<b>Выберите номер FAQ для редактирования:</b>\n\n"
        for idx, faq in enumerate(faqs, 1):
            text += f"{idx}. {faq.question}\n"
        await callback.message.answer(text, parse_mode="HTML")
        await state.set_state(AdminEditFAQ.select_number)
        await state.update_data(faqs=[{'id': f.id, 'question': f.question, 'answer': f.answer} for f in faqs])  # Сохраняем полные данные
    await callback.answer()

@admin_router.message(AdminEditFAQ.select_number)
async def faq_edit_select_number(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Редактирование отменено.", reply_markup=admin_edit_kb)
        return
    data = await state.get_data()
    faqs = data.get('faqs', [])
    try:
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(faqs):
            raise IndexError
        faq = faqs[idx]
        await state.update_data(faq_id=faq['id'], current_question=faq['question'], current_answer=faq['answer'])
        await state.set_state(AdminEditFAQ.question)
        await message.answer(f"Текущий вопрос: {faq['question']}\nВведите новый вопрос :")
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в выборе номера для редактирования FAQ: {e}")
        await message.answer("Некорректный номер. Попробуйте ещё раз или 'отмена'.")

@admin_router.message(AdminEditFAQ.question)
async def faq_edit_question(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Редактирование отменено.", reply_markup=admin_edit_kb)
        return
    question = message.text.strip() if message.text.strip() else (await state.get_data()).get('current_question')
    await state.update_data(question=question)
    await state.set_state(AdminEditFAQ.answer)
    current_answer = (await state.get_data()).get('current_answer')
    await message.answer(f"Текущий ответ: {current_answer}\nВведите новый ответ :")

@admin_router.message(AdminEditFAQ.answer)
async def faq_edit_answer(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Редактирование отменено.", reply_markup=admin_edit_kb)
        return
    answer = message.text.strip() if message.text.strip() else (await state.get_data()).get('current_answer')
    data = await state.get_data()
    faq_id = data.get('faq_id')
    async with async_session_maker() as session:
        dao = DAO(session)
        await dao.update_faq(faq_id, question=data['question'], answer=answer)  # Предполагаю, что в DAO есть метод update_faq(id, question, answer)
    await state.clear()
    await message.answer("FAQ обновлён! ✏️", reply_markup=admin_edit_kb)

# ====== FAQ: удаление (исправлено: отдельное состояние, лучше обработка) ======
@admin_router.callback_query(F.data == "faq_delete")
async def faq_delete_start(callback: types.CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        dao = DAO(session)
        faqs = await dao.get_all_faq()
        if not faqs:
            await callback.answer("FAQ пуст.")
            return
        text = "<b>Выберите номер FAQ для удаления:</b>\n\n"
        for idx, faq in enumerate(faqs, 1):
            text += f"{idx}. {faq.question}\n"
        await callback.message.answer(text, parse_mode="HTML")
        await state.set_state(AdminDeleteFAQ.select_number)  # Отдельное состояние
        await state.update_data(faqs=[{'id': f.id, 'question': f.question} for f in faqs])
    await callback.answer()

@admin_router.message(AdminDeleteFAQ.select_number)
async def faq_delete_confirm(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Удаление отменено.", reply_markup=admin_edit_kb)
        return

    data = await state.get_data()
    faqs = data.get('faqs', [])
    try:
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(faqs):
            raise IndexError
        faq_id = faqs[idx]['id']
        async with async_session_maker() as session:
            dao = DAO(session)
            await dao.delete_faq(faq_id)
        await state.clear()
        await message.answer("FAQ удалён! 🗑️", reply_markup=admin_edit_kb)
        # Опционально: Переотобрази обновленный FAQ
        await show_faq_admin(message)  # Чтобы сразу показать актуальный список
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в удалении FAQ: {e}")
        await message.answer("Некорректный номер. Попробуйте ещё раз или 'отмена'.")
    except Exception as e:
        logging.error(f"Неизвестная ошибка в удалении FAQ: {e}")
        await state.clear()
        await message.answer("Ошибка при удалении. Попробуйте позже.")

# --- Новый механизм ожидания ответа на вопрос ---
reply_waiting = {}

@admin_router.callback_query(F.data.startswith("answer_"))
async def admin_answer_start(callback: types.CallbackQuery):
    admin_id = callback.from_user.id
    if admin_id not in ADMINS_LIST:
        await callback.answer("⛔️ Только админ может отвечать!", show_alert=True)
        return
    user_id = int(callback.data.split('_')[1])
    # Получаем question_id из базы по user_id и тексту вопроса
    question_id = None
    async with async_session_maker() as session:
        dao = DAO(session)
        # Ищем последний вопрос этого пользователя без ответа
        questions = await dao.get_questions_by_user(user_id)
        for q in reversed(questions):
            if not q.answer:
                question_id = q.id
                break
    question_text = callback.message.text
    reply_waiting[admin_id] = {
        "user_id": user_id,
        "chat_id": callback.message.chat.id,
        "message_id": callback.message.message_id,
        "question_text": question_text,
        "question_id": question_id
    }
    await callback.bot.send_message(
        admin_id,
        f"Введите ваш ответ на вопрос или нажмите Отмена.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Отмена", callback_data=f"cancel_reply_{user_id}")]]
        )
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("cancel_reply_"))
async def cancel_reply(callback: types.CallbackQuery):
    reply_waiting.pop(callback.from_user.id, None)
    await callback.message.edit_text("Отмена ответа.")
    await callback.answer()

@admin_router.message()
async def admin_answer_send(message: types.Message):
    if message.chat.type != "private" or message.from_user.id not in ADMINS_LIST:
        return
    waiting = reply_waiting.get(message.from_user.id)
    if not waiting:
        return
    user_id = waiting["user_id"]
    question_id = waiting.get("question_id")
    answer_text = message.text
    # Получаем вопрос из базы
    async with async_session_maker() as session:
        dao = DAO(session)
        question_obj = await dao.get_question(question_id) if question_id else None
    if question_obj:
        question_text = question_obj.question
    else:
        question_text = ""
    # Красивое оформление: приветствие, вопрос и ответ как цитаты
    user_msg = (
        f"Тебе ответили на вопрос!\n\n"
        f"<blockquote>{question_text}</blockquote>\n\n"
        f"Ответ:\n<blockquote>{answer_text}</blockquote>"
    )
    # Красивое оформление для редактируемого сообщения в группе
    chat_username = getattr(question_obj, 'username', None) or 'user'
    chat_msg = (
        f"Вопросик от @{chat_username} закрыт:\n\n"
        f"Вопрос:\n<blockquote>{question_text}</blockquote>\n\n"
        f"Ответ:\n<blockquote>{answer_text}</blockquote>\n\n"
        f"Ответил @{message.from_user.username or 'admin'}"
    )
    import logging
    try:
        await message.bot.send_message(user_id, user_msg, parse_mode="HTML")
        logging.info(f"Ответ отправлен пользователю: user_id={user_id}")
        await message.answer("✅ Ответ отправлен пользователю!")
    except Exception as e:
        logging.error(f"Не удалось отправить ответ пользователю {user_id}: {e}")
        await message.answer(f"❗️ Ошибка: не удалось отправить ответ пользователю. user_id={user_id}")
    try:
        from aiogram.types import InlineKeyboardMarkup
        chat_id = waiting.get("chat_id")
        message_id = waiting.get("message_id")
        logging.info(f"Попытка редактирования сообщения: chat_id={chat_id}, message_id={message_id}")
        await message.bot.edit_message_text(chat_msg, chat_id=chat_id, message_id=message_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
    except Exception as e:
        logging.error(f"Не удалось отредактировать сообщение в чате {chat_id} (message_id={message_id}): {e}")
        await message.answer(f"❗️ Ошибка: не удалось отредактировать сообщение в группе. Проверьте права бота и корректность chat_id/message_id.\nchat_id={chat_id}, message_id={message_id}")
    reply_waiting.pop(message.from_user.id, None)

