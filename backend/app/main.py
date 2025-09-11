from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import videos  # 1. Importe o nosso novo arquivo de rotas

app = FastAPI(title="Video Scene Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Inclua o roteador na aplicação principal, com um prefixo
app.include_router(videos.router, prefix="/api", tags=["Videos"])

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}