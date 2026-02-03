from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

"sqlite:///./chat_crm.db"

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    stage = Column(String, default="onboarding") 

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_or_create_user(db: Session, phone: str):
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True
    return user, False

def save_message(db: Session, user_id: int, role: str, content: str):
    msg = Message(user_id=user_id, role=role, content=content)
    db.add(msg)
    db.commit()

def get_chat_history(db: Session, user_id: int, limit=10):
    # 1. Obtenemos los últimos 10 mensajes (orden descendente por ID para sacar los últimos)
    msgs = db.query(Message).filter(Message.user_id == user_id)\
             .order_by(Message.id.desc()).limit(limit).all()
    
    # 2. Invertimos la lista para que OpenAI lea en orden cronológico (Viejo -> Nuevo)
    # Ejemplo: [Hola (hoy), Hola (ayer)] -> [Hola (ayer), Hola (hoy)]
    history = [{"role": m.role, "content": m.content} for m in reversed(msgs)]
    return history