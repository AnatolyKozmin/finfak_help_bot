from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .models import Question, FAQ, Event, Person, Users

class DAO:
    # --- User ---
    async def add_user(self, tg_id: int, username: str = None):
        result = await self.session.execute(select(Users).where(Users.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            user = Users(tg_id=tg_id, tg_username=username)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user
    async def add_mailing(self, message_id, chat_id, type, text, created_by, created_at):
        from .models import Mailing
        mailing = Mailing(
            message_id=message_id,
            chat_id=chat_id,
            type=type,
            text=text,
            created_by=created_by,
            created_at=created_at
        )
        self.session.add(mailing)
        await self.session.commit()
        await self.session.refresh(mailing)
        return mailing
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Question ---
    async def add_question(self, **kwargs):
        question = Question(**kwargs)
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def get_question(self, question_id: int):
        result = await self.session.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()


    async def get_questions_by_user(self, user_id: int):
        result = await self.session.execute(select(Question).where(Question.user_id == user_id))
        return result.scalars().all()


    async def answer_question(self, question_id: int, answer: str, answer_user_id: int = None, answer_username: str = None):
        await self.session.execute(
            update(Question)
            .where(Question.id == question_id)
            .values(answer=answer, answer_user_id=answer_user_id, answer_username=answer_username)
        )
        await self.session.commit()


    # --- FAQ ---
    async def add_faq(self, question: str, answer: str):
        faq = FAQ(question=question, answer=answer)
        self.session.add(faq)
        await self.session.commit()
        await self.session.refresh(faq)
        return faq


    async def get_all_faq(self):
        result = await self.session.execute(select(FAQ))
        return result.scalars().all()

    async def delete_faq(self, faq_id: int):
        await self.session.execute(delete(FAQ).where(FAQ.id == faq_id))
        await self.session.commit()

    async def update_faq(self, faq_id: int, question: str = None, answer: str = None):
        values = {}
        if question is not None:
            values['question'] = question
        if answer is not None:
            values['answer'] = answer
        await self.session.execute(update(FAQ).where(FAQ.id == faq_id).values(**values))
        await self.session.commit()

    # --- Event ---
    async def add_event(self, **kwargs):
        event = Event(**kwargs)
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event


    async def get_event(self, event_id: int):
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()


    async def get_all_events(self):
        result = await self.session.execute(select(Event))
        return result.scalars().all()


    async def delete_event(self, event_id: int):
        await self.session.execute(delete(Event).where(Event.id == event_id))
        await self.session.commit()

    # --- Person ---
    async def add_person(self, **kwargs):
        person = Person(**kwargs)
        self.session.add(person)
        await self.session.commit()
        await self.session.refresh(person)
        return person


    async def get_person(self, person_id: int):
        result = await self.session.execute(select(Person).where(Person.id == person_id))
        return result.scalar_one_or_none()


    async def get_all_persons(self):
        result = await self.session.execute(select(Person))
        return result.scalars().all()


    async def delete_person(self, person_id: int):
        await self.session.execute(delete(Person).where(Person.id == person_id))
        await self.session.commit()


    async def get_all_user_ids(self):
        # Можно брать user_id из таблицы вопросов, если нет отдельной таблицы пользователей
        result = await self.session.execute(select(Question.user_id).distinct())
        return [row[0] for row in result.all()]
