from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import difflib
import numpy as np

# Conectar ao Qdrant (persistente)
qdrant = QdrantClient(path="./qdrant_db")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def _best_match(collection: str, query_vec: list[float]):
    points, _ = qdrant.scroll(collection_name=collection, limit=1000, with_vectors=True)
    if not points:
        return None
    q = np.array(query_vec, dtype=np.float32)
    def cos(v):
        v = np.array(v, dtype=np.float32)
        denom = (np.linalg.norm(q) * np.linalg.norm(v)) + 1e-9
        return float(np.dot(q, v) / denom)
    best = max(points, key=lambda p: cos(p.vector))
    return best

def query_and_compare(query_text: str):
    """Consulta generated e corrected, e mostra diferenças."""
    query_embedding = embedder.encode(query_text).tolist()
    
    gen = _best_match("generated", query_embedding)
    cor = _best_match("corrected", query_embedding)
    
    if gen and cor:
        gen_text = gen.payload.get("text", "")
        cor_text = cor.payload.get("text", "")
        
        print("Texto Gerado:")
        print(gen_text)
        print("\nTexto Corrigido:")
        print(cor_text)
        print("\nDiferenças:")
        diff = difflib.unified_diff(gen_text.splitlines(), cor_text.splitlines(), lineterm='')
        print('\n'.join(diff))
    else:
        print("Nenhum resultado encontrado.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = sys.argv[1]
        query_and_compare(query)
    else:
        print("Uso: python query_qdrant.py 'sua query'")
    try:
        qdrant.close()
    except Exception:
        pass