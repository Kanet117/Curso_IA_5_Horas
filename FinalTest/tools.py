import json

# 1. DEFINICIÓN DEL ESQUEMA (Lo que ve GPT-4)
# Esto le dice al LLM qué funciones tiene disponibles y qué parámetros requieren.
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "update_lead_info",
            "description": "Utiliza esta función cuando el usuario proporcione su nombre, email o avance en la conversación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "extracted_name": {
                        "type": "string", 
                        "description": "El nombre del usuario si lo menciona."
                    },
                    "extracted_email": {
                        "type": "string", 
                        "description": "El correo electrónico si lo menciona."
                    },
                    "new_stage": {
                        "type": "string", 
                        "enum": ["onboarding", "qualifying", "closing", "closed"],
                        "description": "La nueva fase de venta. Usa 'qualifying' si ya tienes el nombre. Usa 'closing' si ya sabes qué necesita."
                    }
                },
                "required": []
            }
        }
    }
]

# 2. LÓGICA DE EJECUCIÓN (Lo que hace Python)
def execute_tool_call(tool_call, db_session, user_obj):
    """
    Recibe la orden del LLM, ejecuta la función en Python y actualiza la BD.
    """
    fn_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    print(f"🛠️ LLM está ejecutando herramienta: {fn_name} con args: {args}")
    
    if fn_name == "update_lead_info":
        # Actualizamos el objeto Usuario
        if "extracted_name" in args:
            user_obj.name = args["extracted_name"]
        if "extracted_email" in args:
            user_obj.email = args["extracted_email"]
        if "new_stage" in args:
            user_obj.stage = args["new_stage"]
            
        # Guardamos cambios en SQL
        db_session.commit()
        db_session.refresh(user_obj)
        
        return f"Éxito: Datos actualizados. Nombre={user_obj.name}, Etapa={user_obj.stage}"
    
    return "Error: Herramienta no encontrada."