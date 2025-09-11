import os
from fastapi import APIRouter, HTTPException

# Cria um "roteador" para organizar nossos endpoints de vídeo
router = APIRouter()

# Define o caminho base onde os vídeos estão armazenados
# O caminho é relativo à pasta raiz do backend
VIDEOS_BASE_PATH = "videos/"

@router.get("/folders", tags=["Folders"])
def get_folders():
    """
    Escaneia o diretório base de vídeos e retorna uma lista de todas as subpastas.
    """
    try:
        # Lista todos os itens no diretório base
        all_items = os.listdir(VIDEOS_BASE_PATH)
        
        # Filtra a lista para incluir apenas os diretórios
        folders = [
            item for item in all_items 
            if os.path.isdir(os.path.join(VIDEOS_BASE_PATH, item))
        ]
        
        return {"folders": folders}
    except FileNotFoundError:
        # Se a pasta 'videos/' não existir, retorna um erro 404
        raise HTTPException(
            status_code=404, 
            detail=f"Diretório base de vídeos não encontrado em '{VIDEOS_BASE_PATH}'"
        )