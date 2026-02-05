from fastapi import FastAPI, Depends
from interfaces import Mensaje
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import init_db, get_db, get_or_create_user, save_message, get_chat_history

import os

load_dotenv()

# Iniciar FastApi
app = FastAPI()

# Iniciar el cliente chatgpt
client = OpenAI()

# Verificamos que inicie la aplicacion correctamente
@app.on_event("startup")
def startup():
    print("🚀 Iniciando Cerebro...")


@app.post("/mensajes")
def chat(req: Mensaje, db: Session = Depends(get_db)):

    # 1. Obtener usuario + historial (Postgress)
    user, is_new = get_or_create_user(db, req.phone)
    history = get_chat_history(db, user.id, limit=10)

    # 2. Obtener conocimiento de la IA (RAG)

    # 3. Prompt
    prompt = f"""
    Seras un asistente servicial que responde a preguntas.
    """

    mensajes = [
        {"role": "system", "content": prompt},
    ] + history + [
        {"role": "user", "content": req.message}
    ]

    # 4. Respuesta de la IA (Pensamiento)
    respuesta = client.chat.completions.create(
        model="gpt-4o",
        messages=mensajes,
        temperature=0.0
    )

    bot_reply = respuesta.choices[0].message.content

    return {"response": bot_reply}
