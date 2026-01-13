from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.tts_service import TTSService
from fastapi.responses import JSONResponse

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

@router.post("/run-tts")
async def run_tts(request: RunTTSRequest):
    try:
        result = tts_service.run_tts(request.model, request.specialist, request.langs, request.topic_subject, request.selected_topic)
        return {"status": "success", "output": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query-qdrant")
async def query_qdrant(request: QueryQdrantRequest):
    try:
        result = tts_service.query_qdrant(request.query_text)
        return {"status": "success", "data": result}
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