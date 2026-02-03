import requests

# CONFIGURACIÓN
# Esta es la dirección donde vive tu cerebro (main.py)
API_URL = "http://127.0.0.1:8000/webhook"

def iniciar_simulacion():
    print("\n--- 📱 SIMULADOR DE WHATSAPP (CLIENTE) ---")
    print("Este programa simula ser un usuario enviando mensajes a tu API.")
    print("------------------------------------------------------------")

    # 1. Simular Identidad (ID de Usuario)
    # Esto es clave para probar la MEMORIA. Si usas el mismo número, recordará la charla.
    phone_id = input("1. Ingresa un número de celular ficticio (ID): ").strip()
    
    if not phone_id:
        phone_id = "555-TEST-01"
        print(f"   -> Usando ID por defecto: {phone_id}")

    print(f"\n✅ Conectado como: {phone_id}")
    print("   Escribe 'salir' para cerrar o 'borrar' para limpiar pantalla.\n")

    # 2. Bucle de Conversación
    while True:
        try:
            user_message = input("Tú: ").strip()
            
            # Comandos de control
            if user_message.lower() in ['salir', 'exit', 'quit']:
                print("--- Chat finalizado ---")
                break
            if user_message.lower() == 'borrar':
                print("\033[H\033[J") # Limpia consola
                continue
            if not user_message:
                continue

            # 3. Preparar el JSON (Payload)
            # Debe coincidir con la clase WebhookReq en main.py
            payload = {
                "phone": phone_id,
                "message": user_message
            }

            # 4. Enviar al Servidor (Tu API)
            print("   (Enviando...)", end="\r")
            
            # Hacemos la petición POST
            response = requests.post(API_URL, json=payload)
            
            # 5. Procesar Respuesta
            if response.status_code == 200:
                data = response.json()
                # Extraemos el texto de la respuesta del bot
                bot_reply = data.get("response", "Error: La API no devolvió el campo 'response'.")
                
                # Imprimimos bonito
                print(f"🤖 Bot: {bot_reply}\n")
            else:
                print(f"\n❌ Error del Servidor ({response.status_code}):")
                print(f"   {response.text}\n")

        except requests.exceptions.ConnectionError:
            print("\n❌ ERROR DE CONEXIÓN: No se encuentra el servidor.")
            print(f"   ¿Ya corriste 'uvicorn main:app --reload' en otra terminal?")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            break

if __name__ == "__main__":
    iniciar_simulacion()