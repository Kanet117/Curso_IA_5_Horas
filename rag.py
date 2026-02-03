import os
from qdrant_client import QdrantClient, models
from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
client_ai = OpenAI()
qdrant = QdrantClient(location=":memory:") 
COLLECTION_NAME = "solar_knowledge"

def init_vector_db(pdf_path="data/conocimiento.pdf"):
    if not os.path.exists(pdf_path):
        print(f"⚠️ Archivo no encontrado: {pdf_path}")
        return

    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
    )

    print("--- 📄 Procesando PDF con Metadatos ---")
    points = []
    point_id = 0
    pdf_name = os.path.basename(pdf_path)

    reader = PdfReader(pdf_path)
    
    # Iteramos por página para capturar el número de página
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text: continue
        
        # Chunking simple por saltos de línea para no perder contexto de página
        chunks = [t for t in text.split('\n') if len(t) > 30]

        for chunk in chunks:
            # Vectorizamos
            vec = client_ai.embeddings.create(input=chunk, model="text-embedding-3-small").data[0].embedding
            
            # GUARDAMOS METADATOS CLAVE
            payload = {
                "text": chunk,
                "source": pdf_name,
                "page": i + 1  # Guardamos el número de página real
            }

            points.append(models.PointStruct(id=point_id, vector=vec, payload=payload))
            point_id += 1
    
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✅ Indexado: {len(points)} fragmentos de {pdf_name}.")

def search_context(query: str):
    response = client_ai.embeddings.create(input=query, model="text-embedding-3-small")
    hits = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=response.data[0].embedding,
        limit=3
    ).points
    
    if not hits: return ""
    
    # Formateamos el contexto CON los metadatos para que GPT los vea
    context_string = ""
    for hit in hits:
        info = hit.payload
        context_string += f"[Fuente: {info['source']}, Pag: {info['page']}] {info['text']}\n"
        
    return context_string