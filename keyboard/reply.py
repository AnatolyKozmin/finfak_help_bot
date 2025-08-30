from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


################# АДМИНСКИЕ КНОПКИ #########################################################
admin_edit_kb = ReplyKeyboardMarkup(
	keyboard=[
		[
			KeyboardButton(text="✏️ FAQ"),
		],
		[
			KeyboardButton(text="✏️ Мероприятия")
		],
		[
			KeyboardButton(text="✏️ Люди")
		],
        [
			KeyboardButton(text="📥 Рассылка")
		],
	],
	resize_keyboard=True
)


back_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❌ Отмена")
        ]
    ],
	resize_keyboard=True
)


mailing_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Тестовая рассылка"),
        ],
        [
            KeyboardButton(text="Рассылка для всех"),
        ],
    ],
	resize_keyboard=True
)


gaz_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Полетели 🚀"),
        ],
        [
            KeyboardButton(text="❌ Отмена")
        ]
    ],
	resize_keyboard=True
)

################# ЮЗЕРСКИЕ КНОПКИ #########################################################
user_default_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Задать вопрос ✍️")
        ],
        [
            KeyboardButton(text="Мероприятия 💼")
        ],
        [
            KeyboardButton(text="FAQ ❓")
        ],
        [
            KeyboardButton(text="O нас ℹ️")
        ],
    ],
	resize_keyboard=True
)

anon_or_neanon_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Анонимно")
        ],
        [
            KeyboardButton(text="Неанонимно")
        ],
        
        [
            KeyboardButton(text="❌ Отмена")
        ]
    ],
	resize_keyboard=True
)

send_message_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Отправить 🚀"),
        ],
        [
            KeyboardButton(text="❌ Отмена")
        ]
    ]
)