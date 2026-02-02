from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
import os

# Configuración de Clientes
# Usamos OpenAI Estándar (No Async) para facilitar la lectura
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inicializamos Qdrant en MEMORIA para el curso (se borra al reiniciar).
# En producción usar: QdrantClient(url="https://tu-cluster-qdrant...", api_key="...")
qdrant = QdrantClient(location=":memory:") 

COLLECTION_NAME = "knowledge_base"

def init_vector_db():
    """
    1. Crea la colección en Qdrant.
    2. Ingesta documentos base (Simulación de ETL).
    """
    # Verificamos/Recreamos la colección
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
    )
    
    # CONOCIMIENTO BASE DEL NEGOCIO (Lo que el bot debe saber)
    documents = [
        "Somos 'Agencia IA', expertos en automatización de procesos.",
        "Nuestro horario de atención es de Lunes a Viernes de 9:00 AM a 6:00 PM.",
        "Ofrecemos servicios de Chatbots, RAG y Análisis de Datos.",
        "El precio base de una implementación es de $500 USD.",
        "Para soporte técnico escribir a soporte@agenciaia.com.",
        "Aceptamos pagos vía Transferencia, PayPal y Crypto."
    ]
    
    print("--- 🧠 Cargando Memoria Vectorial (RAG) ---")
    
    points = []
    for idx, text in enumerate(documents):
        # 1. Convertir Texto a Números (Embedding)
        response = client_ai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        vector = response.data[0].embedding
        
        # 2. Preparar el punto para Qdrant
        points.append(models.PointStruct(
            id=idx,
            vector=vector,
            payload={"text": text} # Guardamos el texto original para recuperarlo
        ))
        
    # 3. Guardar en Qdrant
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✅ {len(documents)} documentos indexados en Qdrant.")

def search_knowledge(query_text: str, limit: int = 3) -> str:
    """
    Busca información relevante en Qdrant basada en la pregunta del usuario.
    Retorna un string con el contexto encontrado.
    """
    # 1. Vectorizar la pregunta del usuario
    response = client_ai.embeddings.create(
        input=query_text,
        model="text-embedding-3-small"
    )
    query_vector = response.data[0].embedding
    
    # 2. Buscar similitud en Qdrant
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit
    )
    
    # 3. Concatenar resultados
    if not hits:
        return ""
        
    context_str = "\n".join([f"- {hit.payload['text']}" for hit in hits])
    return context_str