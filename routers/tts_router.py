from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.tts_service import TTSService

router = APIRouter()
tts_service = TTSService()

class RunTTSRequest(BaseModel):
    model: str = Field(default="fast", description="Model type: fast or reasoning")
    specialist: Optional[str] = Field(default=None, description="Specialist: grammar or daily")

class QueryQdrantRequest(BaseModel):
    query_text: str = Field(..., description="Query text for search")

@router.post("/run-tts")
async def run_tts(request: RunTTSRequest):
    try:
        result = tts_service.run_tts(request.model, request.specialist)
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