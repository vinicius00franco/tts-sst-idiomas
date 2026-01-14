import sys
from qdrant_client import QdrantClient

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python get_conversation.py <conversation_uuid>")
        sys.exit(1)

    conversation_uuid = sys.argv[1]

    # Conectar ao Qdrant
    qdrant = QdrantClient(path="./qdrant_db")

    try:
        # Buscar o ponto pela ID
        points = qdrant.retrieve(collection_name="conversations", ids=[conversation_uuid])
        if points:
            point = points[0]
            conversation_text = point.payload["text"]
            print(conversation_text)
        else:
            print("Conversa não encontrada")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        qdrant.close()