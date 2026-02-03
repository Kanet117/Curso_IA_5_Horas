from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import json

# Módulos propios (Asegúrate de que existan)
from database import init_db, get_db, get_or_create_user, save_message, get_chat_history
from rag import init_vector_db, search_context
from tools import tools_schema, execute_tool

load_dotenv()
app = FastAPI()
client = OpenAI()

@app.on_event("startup")
def startup():
    print("🚀 Iniciando Cerebro...")
    init_db()
    init_vector_db()

class WebhookReq(BaseModel):
    phone: str
    message: str

@app.post("/webhook")
def chat(req: WebhookReq, db: Session = Depends(get_db)):
    
    # 1. Recuperar Estado (Postgres)
    user, is_new = get_or_create_user(db, req.phone)
    history = get_chat_history(db, user.id, limit=10) # Max 10 mensajes
    
    # 2. Recuperar Contexto (RAG con Metadatos)
    rag_context = search_context(req.message) if len(req.message) > 5 else ""

    # 3. PROMPT ENGINEERING
    system_instruction = f"""
    ### ASIGNACIÓN DE ROL (Persona Pattern) ###
    Eres 'SolarBot', el asistente comercial experto en energía solar de 'SolarTech'.
    Tu tono es profesional, persuasivo pero conciso.

    ### INYECCIÓN DE CONTEXTO (RAG) ###
    Usa EXCLUSIVAMENTE la siguiente información para responder dudas técnicas. 
    Cada fragmento tiene su fuente y página, ÚSALA si es necesario citar.
    
    {rag_context}

    ### DATOS DEL USUARIO ###
    - Nombre: {user.name or 'No identificado'}
    - Etapa actual: {user.stage} (Las etapas son: onboarding -> qualifying -> closed)

    ### INSTRUCCIONES (Chain of Thought / Zero-Shot CoT) ###
    Antes de responder, PIENSA PASO A PASO internamente:
    1. Analiza en qué etapa de venta está el usuario.
    2. Revisa si el usuario te acaba de dar su nombre o correo.
    3. Si te dio datos, DEBES ejecutar la herramienta 'update_lead_info'.
    4. Verifica el contexto RAG. Si la respuesta no está ahí, di que no sabes.
    
    ### FORMATO Y RESTRICCIONES ###
    - Respuestas cortas (máximo 50 palabras).
    - Si usas información del contexto, cita la página así: (Fuente: Pag X).
    
    ### FEW-SHOT PROMPTING (Ejemplos) ###
    Usuario: "Hola"
    Tú: "¡Hola! Bienvenido a SolarTech. Soy SolarBot. Para empezar, ¿cuál es tu nombre?"
    
    Usuario: "Me llamo Juan"
    Tú (Tool call): update_lead_info(name="Juan", stage="qualifying")
    Tú (Respuesta): "Gracias Juan. ¿Buscas paneles para Casa o Industria?"

    ### NEGATIVE PROMPTING ###
    - NO inventes precios que no estén en el contexto.
    - NO saludes de nuevo si ya hay historial reciente.
    - NO pidas el correo si estás en etapa 'onboarding', primero el nombre.
    """

    messages_payload = [
        {"role": "system", "content": system_instruction}
    ] + history + [{"role": "user", "content": req.message}]

    # 4. PRIMERA LLAMADA (PENSAMIENTO)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages_payload,
        tools=tools_schema,
        tool_choice="auto",
        temperature=0.0
    )
    
    ai_msg = response.choices[0].message
    final_text = ai_msg.content

    # 5. EJECUCIÓN DE TOOLS (CORREGIDO ✅)
    if ai_msg.tool_calls:
        print(f"🛠️ El Bot quiere ejecutar {len(ai_msg.tool_calls)} herramientas.")
        
        # A) Agregamos la intención del asistente AL HISTORIAL UNA SOLA VEZ
        messages_payload.append(ai_msg)

        # B) Ejecutamos TODAS las herramientas que pidió
        for tool in ai_msg.tool_calls:
            # Ejecutar lógica Python
            result = execute_tool(tool, db, user)
            
            # Agregar el resultado de ESTA herramienta específica
            messages_payload.append({
                "role": "tool", 
                "tool_call_id": tool.id, 
                "content": str(result)
            })

        # C) Hacemos la SEGUNDA llamada UNA SOLA VEZ (con todos los resultados listos)
        resp_2 = client.chat.completions.create(
            model="gpt-4o", messages=messages_payload
        )
        final_text = resp_2.choices[0].message.content

    # 6. GUARDAR HISTORIAL
    if final_text:
        save_message(db, user.id, "user", req.message)
        save_message(db, user.id, "assistant", final_text)

    return {"response": final_text}