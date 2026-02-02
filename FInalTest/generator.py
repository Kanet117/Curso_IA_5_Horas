from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
import os

# Importamos nuestros módulos propios
from database import init_sql_db, get_db, User, Message
from vector_db import init_vector_db, search_knowledge
from FInalTest.tools import tools_schema, execute_tool_call

# Inicializamos App y Cliente OpenAI
app = FastAPI(title="Agente Cognitivo Modular MIT")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- STARTUP (Arranque) ---
@app.on_event("startup")
def on_startup():
    """Inicializa ambas bases de datos al encender el servidor."""
    print("--- INICIANDO SISTEMA ---")
    init_sql_db()    # Crear tablas SQL
    init_vector_db() # Crear índices Vectoriales (Qdrant)
    print("--- SISTEMA LISTO ---")

# --- API ENDPOINTS ---

class WebhookRequest(BaseModel):
    phone: str
    message: str

@app.post("/webhook")
def chat_endpoint(req: WebhookRequest, db: Session = Depends(get_db)):
    """
    Flujo Principal del Agente:
    1. Identificación (SQL)
    2. Memoria (SQL)
    3. Contexto (RAG/Qdrant)
    4. Razonamiento (OpenAI)
    5. Acción (Tools)
    6. Respuesta
    """
    print(f"\n📨 Mensaje recibido de {req.phone}: {req.message}")

    # 1. IDENTIFICACIÓN O REGISTRO
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        user = User(phone=req.phone, stage="onboarding")
        db.add(user)
        db.commit()
        print(" -> Usuario Nuevo creado.")

    # 2. RECUPERAR MEMORIA (Últimos 5 mensajes)
    # Importante: OpenAI lee de arriba hacia abajo, revertimos el orden para que sea cronológico
    history_objs = db.query(Message).filter(Message.user_phone == req.phone).order_by(Message.id.desc()).limit(5).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(history_objs)]

    # 3. RAG: BUSCAR EN CONOCIMIENTO
    # Solo buscamos si el mensaje tiene más de 3 palabras para ahorrar costos
    rag_context = ""
    if len(req.message.split()) > 2:
        rag_context = search_knowledge(req.message)
        if rag_context:
            print(f" -> 🧠 RAG encontró contexto relevante.")

    # 4. CONSTRUIR EL PROMPT DE SISTEMA (Dinámico)
    system_instruction = f"""
    Eres Ana, la IA de ventas de 'Agencia IA'.
    
    INFORMACIÓN DEL CLIENTE:
    - Nombre: {user.name or 'No identificado'}
    - Etapa Actual: {user.stage}
    
    BASE DE CONOCIMIENTO (Usa esto para responder preguntas):
    {rag_context}
    
    TUS INSTRUCCIONES ACTUALES SEGÚN ETAPA:
    - Si etapa es 'onboarding': Saluda amablemente y consigue su nombre.
    - Si etapa es 'qualifying': Averigua qué servicio necesita y responde dudas usando la Base de Conocimiento.
    - Si etapa es 'closing': Pide su email para agendar una reunión.
    
    REGLA: Usa la herramienta 'update_lead_info' SIEMPRE que el usuario te diga su nombre, email o cambies de fase.
    """

    messages_payload = [{"role": "system", "content": system_instruction}] + history + [{"role": "user", "content": req.message}]

    # 5. LLAMADA A OPENAI (Síncrona)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages_payload,
        tools=tools_schema,
        tool_choice="auto", # El modelo decide si usa herramientas o habla normal
        temperature=0.2
    )

    ai_msg = response.choices[0].message
    final_text = ai_msg.content

    # 6. MANEJO DE HERRAMIENTAS (Si el cerebro decidió usar una tool)
    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            # Ejecutar la acción en Python
            result_msg = execute_tool_call(tool_call, db, user)
            
            # (Opcional) Podríamos volver a llamar a OpenAI con el resultado,
            # pero para el curso básico, si actualizamos datos, confirmamos simple.
            if not final_text:
                final_text = "¡Perfecto! He actualizado tu información."

    # 7. GUARDAR INTERACCIÓN Y RESPONDER
    if final_text:
        # Guardar User Msg
        db.add(Message(user_phone=req.phone, role="user", content=req.message))
        # Guardar AI Msg
        db.add(Message(user_phone=req.phone, role="assistant", content=final_text))
        db.commit()

    return {"response": final_text}

# Para correr: uvicorn main:app --reload