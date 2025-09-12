import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api import videos
from app.api import search

from app.api import management # 1. Importe o novo arquivo

# --- [NOVO] INICIALIZAÇÃO E CRIAÇÃO DE DIRETÓRIOS ---
# Define o caminho base da pasta 'backend'
BASE_DIR = Path(__file__).resolve().parent.parent

# Define os caminhos para as pastas que a aplicação precisa
VIDEOS_DIR = BASE_DIR / "videos"
CLIPS_DIR = BASE_DIR / "clips"

# Garante que as pastas essenciais existam ao iniciar a aplicação
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)
# --- FIM DA NOVA SEÇÃO ---

app = FastAPI(title="Video Scene Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta a pasta de clipes como um diretório estático
# Agora a pasta 'clips' já foi criada, então este comando não falhará
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")

# Inclui os roteadores da API
app.include_router(videos.router, prefix="/api", tags=["Media & Processing"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(management.router, prefix="/api", tags=["Management"]) # 4. Adicione o novo roteador

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}