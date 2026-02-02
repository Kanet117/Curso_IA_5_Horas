from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Creamos el cliente (Objeto con todas las variables, funciones o clases necearias para usar IA)
client = OpenAI(api_key=os.getenv("GPT_API_KEY"))

# Generamos una sola respuesta
respuesta = client.responses.create(
    model = "gpt-4o-mini", # Modelo de IA a utilizar
    input = "Dime como me llamo." # Pregunta que el usuario hace
)

# Respuesta
print(respuesta)
