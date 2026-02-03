import requests

API_URL = "http://127.0.0.1:8000/mensajes"

def iniciar_simulacion():
    print("--- Simulador de WhatsApp (Cliente / frontend) ---\n\n")

    phone_id = input("Ingresa tu numero de celular (ID): ").strip()

    if not phone_id:
        phone_id = "555"
        print("Usando ID por defecto: 555")
    
    print("Escribe 'Salir' para cerrar o 'borrar' para limpiar la pantalla.\n")

    while True:
        try:
            user_message = input("Tú: ").strip()

            if user_message.lower() == "salir":
                print("--- Chat finalizado ---")
                break
            if user_message.lower() == "borrar":
                print("\033[H\033[J")
                continue
            if not user_message:
                continue

            payload = {
                "phone": phone_id,
                "message": user_message
            }

            print("     (Enviando...)", end="\r")

            # Enviamos el mensaje a la IA
            response = requests.post(API_URL, json=payload)

            # Procesar la respuesta
            if response.status_code == 200:
                respuesta = response.json()
                bot_reply = respuesta.get("response")
                print(f"Bot: {bot_reply}\n")
        except Exception as e:
            print(f"\n Error inesperado {e}")
            break

if __name__ == "__main__":
    iniciar_simulacion()