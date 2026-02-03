from fastapi import FastAPI, Depends
from interfaces import Mensaje
from openai import OpenAI
from dotenv import load_dotenv
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
def chat(req: Mensaje):

    # 1. Obtener usuario + historial (Postgress)

    # 2. Obtener conocimiento de la IA (RAG)

    # 3. Prompt
    prompt = f"""
    Seras un asistente servicial que responde a preguntas.
    """

    mensajes = [
        {"role": "developer", "content": prompt},
        {"role": "user",   "content": req.message}
    ]

    # 4. Respuesta de la IA (Pensamiento)
    respuesta = client.chat.completions.create(
        model="gpt-4o",
        messages=mensajes,
        temperature=0.0
    )

    bot_reply = respuesta.choices[0].message.content

    return {"response": bot_reply}
