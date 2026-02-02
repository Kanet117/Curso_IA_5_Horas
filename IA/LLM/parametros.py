from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Creamos el cliente (Objeto con todas las variables, funciones o clases necearias para usar IA)
client = OpenAI(api_key=os.getenv("GPT_API_KEY"))

# Generamos una sola respuesta
respuesta = client.responses.create(
    model = "gpt-4o-mini", # Modelo de IA a utilizar
    input = "Dime como me llamo.", # Pregunta que el usuario hace
    temperature=.7,
    max_output_tokens=500,
    max_tool_calls=3,
    instructions="none",
    stream=True,
    top_p=3,
    timeout=200,
    reasoning=True
)

# Respuesta
print(respuesta)
