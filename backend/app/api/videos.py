import os
import uuid
from fastapi import APIRouter, HTTPException
from fastapi import BackgroundTasks, WebSocket, WebSocketDisconnect
# Substitua o placeholder pela sua função real
from app.services.processing_service import run_scene_detection # Placeholder
from app.core.websockets import manager

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
    
@router.post("/process/{folder_name}/{filename}", status_code=202, tags=["Processing"])
async def process_video(folder_name: str, filename: str, background_tasks: BackgroundTasks):
    """
    Inicia o processo de detecção de cena para um vídeo em segundo plano.
    """
    video_path = os.path.join(VIDEOS_BASE_PATH, folder_name, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    job_id = str(uuid.uuid4())

    async def progress_callback(data: dict):
        await manager.send_json(job_id, data)

    # Adiciona a tarefa pesada para ser executada em segundo plano
    # O primeiro argumento da função run_scene_detection é o video_path
    # O segundo é a pasta de saída (a mesma do vídeo)
    # O terceiro é o nosso callback
    background_tasks.add_task(run_scene_detection, video_path, os.path.join(VIDEOS_BASE_PATH, folder_name), progress_callback)
    
    return {"job_id": job_id, "message": "Processamento iniciado"}


@router.websocket("/ws/progress/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            # Mantém a conexão aberta para receber mensagens do backend
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)