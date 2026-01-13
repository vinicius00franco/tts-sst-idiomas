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
- `POST /api/v1/suggest-topics`: Sugere tópicos em PT-BR para um assunto, considerando modelo e especialista.
- `POST /api/v1/run-tts`: Executa `scripts/run_tts.py` com parâmetros `model`, `specialist`, `langs`, `topic_subject`, `selected_topic`.
- `POST /api/v1/query-qdrant`: Executa `scripts/query_qdrant.py` com `query_text`.

## Testes
Use o arquivo `api_tests.http` para testar as rotas com cenários válidos e de erro.
- Abra o arquivo no VS Code com extensão REST Client.
- Execute os requests para validar fluxos e erros.

### Fluxo Lógico Esperado
1. **Sugestão de Tópicos**: POST `/api/v1/suggest-topics` com `subject` para obter opções em PT-BR.
2. **Geração de TTS**: POST `/api/v1/run-tts` com `selected_topic` de 1, gerando áudios e salvando no Qdrant.
3. **Consulta Qdrant**: POST `/api/v1/query-qdrant` para comparar versões geradas vs corrigidas.

Exemplo de request para run-tts:
```json
{
  "model": "fast",
  "specialist": "daily",
  "langs": ["en"],
  "selected_topic": "Desenvolvimento da IA generativa"
}
```