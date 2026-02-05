from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

DATABASE_URL = "sqlite:///./chat_crm.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Tabla usuarios
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    paso = Column(String, default="inicio")

class Mensaje(Base):
    __tablename__ = "mensajes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal
    try: yield db
    finally: db.close()

def get_or_create_user(db: Session, phone: str):
    user = db.query(User).filter(User.phone == phone).fist()
    if not user:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True
    return user, False

def save_message(db: Session, user_id: int, role: str, content: str):
    msg = Mensaje(user_id=user_id, role=role, content=content)
    db.add(msg)
    db.commit()

def get_chat_history(db: Session, user_id: int, limit = 10):
    msgs = db.query(Mensaje).filter(Mensaje.user_id == user_id).order_by(Mensaje.id.desc()).limit(limit).all()
    history = []
    for msg in reversed(msgs):
        history.append(
            {
                "role": msg.role,
                "content": msg.content
            }
        )
    return history