from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# CONFIGURACIÓN
# Usamos SQLite por defecto para facilitar el curso. 
# En producción cambiar a: "postgresql://user:pass@localhost/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm_chat.db")

# check_same_thread=False es necesario solo para SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (Tablas) ---

class User(Base):
    """La entidad del Cliente Potencial (Lead)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)  # ID de WhatsApp
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Estados: 'onboarding' -> 'qualifying' -> 'closing' -> 'closed'
    stage = Column(String, default="onboarding") 

class Message(Base):
    """El historial del chat (Memoria)"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_phone = Column(String, index=True)
    role = Column(String) # 'user' o 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- FUNCIONES DE UTILIDAD ---

def init_sql_db():
    """Crea las tablas si no existen."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Inyección de dependencia para obtener sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()