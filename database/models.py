from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
import enum
from sqlalchemy import Enum as PgEnum
from database.engine import Base


class MailingType(enum.Enum):
	text = "text"
	photo = "photo"
	video = "video"
	round = "round"


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String, nullable=True)
    question = Column(String, nullable=False)
    is_anon = Column(Boolean, default=True)
    group_message_id = Column(BigInteger, nullable=True)
    answer = Column(String, nullable=True)
    answer_user_id = Column(BigInteger, nullable=True)
    answer_username = Column(String, nullable=True)


class FAQ(Base):
    __tablename__ = 'faq'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_username = Column(String, nullable=True)
    tg_id = Column(BigInteger, nullable=False)


class Mailing(Base):
	__tablename__ = 'mailings'
	id = Column(Integer, primary_key=True, autoincrement=True)
	message_id = Column(BigInteger, nullable=False)
	chat_id = Column(BigInteger, nullable=False)
	type = Column(PgEnum(MailingType), nullable=False)
	text = Column(Text, nullable=True)
	created_by = Column(BigInteger, nullable=False)  # user_id админа
	created_at = Column(DateTime, nullable=False)
	file_id = Column(String, nullable=True)  # Telegram file_id


class Event(Base):
	__tablename__ = 'events'
	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(String, nullable=False)
	description = Column(Text, nullable=True)
	date = Column(DateTime, nullable=False)
	location = Column(String, nullable=True)
	created_by = Column(BigInteger, nullable=True)  # user_id администратора
	file_id = Column(String, nullable=True)  # Telegram file_id
      

# Люди
class Person(Base):
	__tablename__ = 'persons'
	id = Column(Integer, primary_key=True, autoincrement=True)
	last_name = Column(String, nullable=False)
	first_name = Column(String, nullable=False)
	contact = Column(String, nullable=True)
	position = Column(String, nullable=True)
	photo = Column(String, nullable=True)  # путь к файлу или url
	file_id = Column(String, nullable=True)  # Telegram file_id