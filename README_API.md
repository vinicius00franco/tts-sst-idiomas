# TTS-SST API

API FastAPI para executar scripts de TTS e consulta Qdrant.

## Estrutura
- `main.py`: App FastAPI principal.
- `routers/tts_router.py`: Rotas para TTS.
- `services/tts_service.py`: Serviço para executar scripts.

## Como rodar
1. Ative o venv: `source venv/bin/activate`
2. Rode o servidor: `uvicorn main:app --reload`
3. Acesse http://127.0.0.1:8000/docs para Swagger UI.

## Rotas
- `POST /api/v1/run-tts`: Executa `scripts/run_tts.py` com parâmetros `model` e `specialist`.
- `POST /api/v1/query-qdrant`: Executa `scripts/query_qdrant.py` com `query_text`.

Exemplo de request para run-tts:
```json
{
  "model": "fast",
  "specialist": "grammar"
}
```