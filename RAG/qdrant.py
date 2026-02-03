import os
import uuid
from typing import List, Dict
from pypdf import PdfReader
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class Qdrant:
    
    # 1. Configuración Inicial
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    client = QdrantClient(":memory:")
    COLLECTION_NAME = "PDFs"

    @staticmethod
    def initialize_collection(vector_size: int = 384):
        """Crea la colección en Qdrant si no existe."""
        if not Qdrant.client.collection_exists(Qdrant.COLLECTION_NAME):
            Qdrant.client.create_collection(
                collection_name=Qdrant.COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """
        Genera el vector (embedding) para un texto.
        Usamos list() para convertir el generador y tomamos el indice 0.
        """
        # El modelo espera una lista de textos, por eso los corchetes [text]
        embeddings_generator = Qdrant.embedding_model.embed([text])
        embeddings_list = list(embeddings_generator)
        return embeddings_list[0]

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extrae texto plano de un PDF dado su path."""
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"Error al leer el PDF: {e}")
            return ""
        return text

    @staticmethod
    def chunks_with_overlap(text: str, max_length: int = 500, overlap: int = 50) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + max_length, text_length)
            chunk = text[start:end].strip()
            if len(chunk) > 10:
                chunks.append(chunk)
            start += max_length - overlap
        return chunks

    @staticmethod
    def upload_single_pdf(file_path: str):
        """Sube un solo PDF a Qdrant."""
        if not os.path.exists(file_path):
            print(f"Error: El archivo '{file_path}' no existe.")
            return

        Qdrant.initialize_collection()
        print(f"Procesando archivo: {file_path}...")

        # 1. Extraer
        full_text = Qdrant.extract_text_from_pdf(file_path)
        if not full_text: return

        # 2. Chunking
        chunks = Qdrant.chunks_with_overlap(full_text)
        print(f" -> Se generaron {len(chunks)} fragmentos.")

        # 3. Embeddings 
        embeddings = list(Qdrant.embedding_model.embed(chunks))

        # 4. Subir
        points = []
        file_name = os.path.basename(file_path)
        
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={
                    "source": file_name,
                    "text": chunk,
                    "chunk_id": i
                }
            ))

        Qdrant.client.upsert(
            collection_name=Qdrant.COLLECTION_NAME,
            points=points
        )
        print(f" -> Archivo '{file_name}' cargado.")

    @staticmethod
    def search(query: str, top_k: int = 3) -> List[Dict]:
        """Busca los fragmentos más relevantes."""
        
        # 1. Usamos la nueva funcion para obtener el vector de la pregunta
        query_vector = Qdrant.get_embedding(query)

        # 2. Buscar
        search_result = Qdrant.client.search(
            collection_name=Qdrant.COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )

        # 3. Formatear
        results = []
        for item in search_result:
            results.append({
                "score": item.score,
                "text": item.payload.get("text"),
                "source": item.payload.get("source")
            })
        
        return results


# --- PRUEBAS ---

# 1. Nombre de tu archivo PDF
mi_pdf = "conocimiento/documento_ejemplo.pdf"

# 2. Subirlo
Qdrant.upload_single_pdf(mi_pdf)

# 3. Preguntar
pregunta = "¿Cuáles son los puntos clave?"
print(f"\nPreguntando: {pregunta}...")

resultados = Qdrant.search(pregunta, top_k=1)

print(resultados)