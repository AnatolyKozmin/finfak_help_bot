from aiogram.fsm.state import State, StatesGroup


# FSM для добавления FAQ
class AdminAddFAQ(StatesGroup):
    question = State()
    answer = State()


# FSM для редактирования FAQ
class AdminEditFAQ(StatesGroup):
    select_number = State()  # Выбор номера FAQ для редактирования
    question = State()
    answer = State()


# FSM для удаления FAQ
class AdminDeleteFAQ(StatesGroup):
    select_number = State()  # Выбор номера FAQ для удаления


# FSM для добавления Event
class AdminAddEvent(StatesGroup):
    title = State()
    description = State()
    date = State()
    location = State()
    file_id = State()  # Для фото или документа


# FSM для редактирования Event
class AdminEditEvent(StatesGroup):
    event_id = State()  # ID мероприятия для редактирования
    title = State()
    description = State()
    date = State()
    location = State()
    file_id = State()
    created_by = State()  # Оставлено для совместимости, но можно убрать, если не редактируется


# FSM для добавления Person
class AdminAddPerson(StatesGroup):
    last_name = State()
    first_name = State()
    position = State()
    contact = State()
    file_id = State()  # Для фото или документа


# FSM для редактирования Person
class AdminEditPerson(StatesGroup):
    person_id = State()  # ID человека для редактирования
    last_name = State()
    first_name = State()
    position = State()
    contact = State()
    file_id = State()  # Для фото или документа


# FSM для рассылки сообщений
class AdminMailing(StatesGroup):
    content_type = State()  # Тип контента (текст, фото, видео и т.д.)
    confirm_type = State()  # Выбор тестовой/массовой рассылки
    confirm_all = State()   # Подтверждение массовой рассылки