from fastapi import FastAPI
from fastapi.responses import Response
from routers.tts_router import router as tts_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="TTS-SST API", version="1.0.0")

# CORS para permitir acesso da página web local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tts_router, prefix="/api/v1", tags=["TTS"])

# Servir UI estática em /web
app.mount("/web", StaticFiles(directory="web"), name="web")

# Servir saídas (áudios/transcrições) em /outputs
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Catch-all OPTIONS for API to satisfy preflight even when Origin handling varies
@app.options("/api/v1/{path:path}")
async def options_any(path: str):
    return Response(status_code=200)

@app.get("/")
async def root():
    return {"message": "TTS-SST API is running"}