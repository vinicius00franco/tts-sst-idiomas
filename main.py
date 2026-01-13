from fastapi import FastAPI
from routers.tts_router import router as tts_router

app = FastAPI(title="TTS-SST API", version="1.0.0")

app.include_router(tts_router, prefix="/api/v1", tags=["TTS"])

@app.get("/")
async def root():
    return {"message": "TTS-SST API is running"}