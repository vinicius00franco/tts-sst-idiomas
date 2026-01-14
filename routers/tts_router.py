import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.tts_service import TTSService
from fastapi.responses import JSONResponse
from fastapi import Query

router = APIRouter()
tts_service = TTSService()

class RunTTSRequest(BaseModel):
    model: str = Field(default="fast", description="Model type: fast or reasoning")
    specialist: Optional[str] = Field(default=None, description="Specialist: grammar or daily")
    langs: list[str] = Field(default_factory=lambda: ["en", "es"], description="Languages to generate: en, es")
    topic_subject: Optional[str] = Field(default=None, description="Subject to suggest topics")
    selected_topic: Optional[str] = Field(default=None, description="Selected topic text for generation")

class QueryQdrantRequest(BaseModel):
    query_text: str = Field(..., description="Query text for search")

class GetConversationRequest(BaseModel):
    conversation_uuid: str = Field(..., description="UUID of the conversation to retrieve")

@router.post("/run-tts")
async def run_tts(request: RunTTSRequest):
    try:
        result = tts_service.run_tts(request.model, request.specialist, request.langs, request.topic_subject, request.selected_topic)
        payload = {"status": "success", "output": result}
        # Tentar extrair o JSON final, se presente
        try:
            last_line = [ln for ln in result.strip().splitlines() if ln.strip()][-1]
            data = json.loads(last_line)
            payload.update(data)
        except Exception:
            pass
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query-qdrant")
async def query_qdrant(request: QueryQdrantRequest):
    try:
        result = tts_service.query_qdrant(request.query_text)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-conversation")
async def get_conversation(request: GetConversationRequest):
    try:
        result = tts_service.get_conversation(request.conversation_uuid)
        return {"status": "success", "conversation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SuggestTopicsRequest(BaseModel):
    model: str = Field(default="fast")
    specialist: Optional[str] = Field(default=None)
    lang: str = Field(default="en")
    subject: str = Field(...)

@router.post("/suggest-topics")
async def suggest_topics(request: SuggestTopicsRequest):
    @router.options("/suggest-topics")
    async def options_suggest_topics():
        return JSONResponse(content={})

    @router.options("/run-tts")
    async def options_run_tts():
        return JSONResponse(content={})

    @router.options("/query-qdrant")
    async def options_query_qdrant():
        return JSONResponse(content={})
    try:
        topics = tts_service.suggest_topics(request.model, request.specialist, request.lang, request.subject)
        return {"status": "success", "topics": topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-tts")
async def latest_tts(lang: Optional[str] = Query(default=None, description="Filtrar por língua: en ou es")):
    """Retorna o último áudio gerado em outputs/ e sua transcrição se existir."""
    try:
        outputs_dir = "outputs"
        if not os.path.isdir(outputs_dir):
            raise HTTPException(status_code=404, detail="Outputs não encontrados")

        # Listar FLACs e ordenar por mtime desc
        flacs = []
        for name in os.listdir(outputs_dir):
            if not name.lower().endswith(".flac"):
                continue
            if lang and f"interview_{'english' if lang=='en' else 'spanish'}" not in name:
                continue
            path = os.path.join(outputs_dir, name)
            flacs.append((path, os.path.getmtime(path)))
        if not flacs:
            raise HTTPException(status_code=404, detail="Nenhum áudio encontrado")
        flacs.sort(key=lambda x: x[1], reverse=True)
        latest_path, _ = flacs[0]
        rel_name = os.path.basename(latest_path)
        # Mapear língua por basename
        if "english" in rel_name:
            detected_lang = "en"
        elif "spanish" in rel_name:
            detected_lang = "es"
        else:
            detected_lang = None

        json_path = latest_path[:-5] + ".json"
        transcript = None
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    transcript = data.get("lines") or data
            except Exception:
                transcript = None

        return {
            "status": "success",
            "audio": {
                "name": rel_name,
                "url": f"/outputs/{rel_name}",
                "lang": detected_lang,
            },
            "transcript": transcript,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))