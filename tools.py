import smtplib
import os
import json
from email.mime.text import MIMEText
from sqlalchemy.orm import Session

# 1. Definición para OpenAI
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "update_lead_info",
            "description": "Guarda o actualiza el nombre, email o etapa del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "stage": {"type": "string", "enum": ["onboarding", "interested", "closed"]}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Envía un correo electrónico con información al usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to_email", "subject", "body"]
            }
        }
    }
]

# 2. Lógica Python

def send_email_action(to_email, subject, body):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    
    if not sender or not password:
        return "Error: Credenciales de correo no configuradas en el servidor."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return "Correo enviado exitosamente."
    except Exception as e:
        return f"Error enviando correo: {str(e)}"

def execute_tool(tool_call, db: Session, user):
    fn_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    print(f"🛠️ Ejecutando Tool: {fn_name} | Args: {args}")

    if fn_name == "update_lead_info":
        if "name" in args: user.name = args["name"]
        if "email" in args: user.email = args["email"]
        if "stage" in args: user.stage = args["stage"]
        db.commit()
        return "Información actualizada en base de datos."

    elif fn_name == "send_email":
        return send_email_action(args["to_email"], args["subject"], args["body"])
    
    return "Herramienta no encontrada"