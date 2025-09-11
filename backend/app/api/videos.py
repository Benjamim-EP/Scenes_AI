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
    
@router.get("/videos/{folder_name}", tags=["Videos"])
def get_videos_in_folder(folder_name: str):
    """
    Lista os arquivos de vídeo em uma pasta específica e verifica o status de processamento.
    """
    folder_path = os.path.join(VIDEOS_BASE_PATH, folder_name)

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Pasta não encontrada")

    supported_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm', '.mpg')
    videos = []

    try:
        for filename in os.listdir(folder_path):
            # Considera apenas arquivos com as extensões suportadas
            if filename.lower().endswith(supported_extensions):
                base_name, _ = os.path.splitext(filename)
                
                # O JSON de cenas é salvo na mesma pasta do vídeo por padrão,
                # podemos mudar isso no futuro se necessário.
                json_path = os.path.join(folder_path, f"{base_name}_cenas.json")
                
                video_info = {
                    "filename": filename,
                    "folder": folder_name,
                    "has_scenes_json": os.path.exists(json_path),
                    # Futuramente, podemos adicionar "is_in_database": True/False
                }
                videos.append(video_info)
        
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler a pasta: {e}")