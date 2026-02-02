from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Creamos el cliente (Objeto con todas las variables, funciones o clases necearias para usar IA)
client = OpenAI(api_key=os.getenv("GPT_API_KEY"))

# Roles
["user", "assistant", "developer"]

# Generamos una sola respuesta
respuesta = client.responses.create(
    model="gpt-5",
    reasoning={"effort": "low"},
    instructions="",
    input=[
        {
            "role": "developer",
            "content": "Talk like a pirate."
        },
        {
            "role": "user",
            "content": "Are semicolons optional in JavaScript?"
        },
        {
            "role": "assistant", 
            "content": "Who's there?"
        },
        {
            "role": "user", 
            "content": "Orange."
        },
    ]
)

# Respuesta
print(respuesta)
