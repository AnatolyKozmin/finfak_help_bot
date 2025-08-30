from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Кнопки для пагинации и действий над объектами (мероприятия, люди, рассылки)
def get_admin_pagination_kb(object_type: str, object_id: int = None):
    # object_type: 'event', 'person', 'mailing'
    # object_id нужен для callback data
    buttons = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"{object_type}_prev"),
            InlineKeyboardButton(text="➡️", callback_data=f"{object_type}_next"),
        ],
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data=f"{object_type}_add"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"{object_type}_edit_{object_id}" if object_id else f"{object_type}_edit"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"{object_type}_delete_{object_id}" if object_id else f"{object_type}_delete"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Пример использования:
# markup = get_admin_pagination_kb('event', event_id)
# markup = get_admin_pagination_kb('person', person_id)
# markup = get_admin_pagination_kb('mailing', mailing_id)

# Для FAQ можно сделать только действия без пагинации
faq_admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="faq_add"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="faq_edit"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data="faq_delete"),
        ]
    ]
)
