import os
import shutil
import subprocess
import uuid
from pathlib import Path
import mimetypes
import json

from fastapi import (APIRouter, BackgroundTasks, HTTPException, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import FileResponse

from app.core.websockets import manager
# Supondo que seu serviço de processamento esteja pronto e importável
# Se o arquivo ainda não existe, crie um placeholder ou comente esta linha
from app.services.processing_service import run_scene_detection

# ==============================================================================
# --- CONFIGURAÇÃO DO ROTEADOR E CAMINHOS ---
# ==============================================================================
router = APIRouter()

# Usando pathlib para uma manipulação de caminhos mais robusta
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Vai para a raiz da pasta /backend
VIDEOS_BASE_PATH = BASE_DIR / "videos"
THUMBNAIL_CACHE_PATH = VIDEOS_BASE_PATH / ".thumbnails" # Pasta oculta para cache

# Cria a pasta de cache de thumbnails na inicialização, se não existir
os.makedirs(THUMBNAIL_CACHE_PATH, exist_ok=True)


# ==============================================================================
# --- ENDPOINTS DE LISTAGEM ---
# ==============================================================================

@router.get("/folders", tags=["Folders"], summary="Lista todas as pastas de vídeo de primeiro nível")
def get_folders():
    """
    Escaneia o diretório base de vídeos e retorna uma lista de todas as subpastas.
    """
    try:
        all_items = os.listdir(VIDEOS_BASE_PATH)
        folders = [
            item for item in all_items
            if os.path.isdir(VIDEOS_BASE_PATH / item) and not item.startswith('.')
        ]
        return {"folders": sorted(folders)}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Diretório base de vídeos não encontrado em '{VIDEOS_BASE_PATH}'"
        )


@router.get("/videos/{folder_name}", tags=["Videos"], summary="Lista os vídeos em uma pasta específica")
def get_videos_in_folder(folder_name: str):
    """
    Lista os arquivos de vídeo em uma pasta específica e verifica o status de processamento.
    """
    folder_path = VIDEOS_BASE_PATH / folder_name
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Pasta não encontrada")

    supported_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm', '.mpg', '.wmv')
    videos = []

    try:
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(supported_extensions):
                base_name, _ = os.path.splitext(filename)
                
                # O JSON de cenas é salvo na mesma pasta do vídeo por padrão
                json_path = folder_path / f"{base_name}_cenas.json"
                
                video_info = {
                    "filename": filename,
                    "folder": folder_name,
                    "has_scenes_json": os.path.exists(json_path),
                }
                videos.append(video_info)
        
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler a pasta: {e}")


# ==============================================================================
# --- ENDPOINTS DE MÍDIA (THUMBNAILS E STREAMING) ---
# ==============================================================================

@router.get("/thumbnail/{folder_name}/{filename}", tags=["Media"], summary="Gera e serve uma thumbnail")
def get_thumbnail(folder_name: str, filename: str):
    """
    Gera uma thumbnail para um vídeo (se não existir no cache) e a serve como um arquivo de imagem.
    """
    video_path = VIDEOS_BASE_PATH / folder_name / filename
    thumbnail_filename = f"{os.path.splitext(filename)[0]}.jpg"
    thumbnail_path = THUMBNAIL_CACHE_PATH / thumbnail_filename

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    if not os.path.exists(thumbnail_path):
        try:
            # Comando FFmpeg para extrair um frame de forma eficiente
            command = [
                'ffmpeg', '-ss', '5', '-i', str(video_path),
                '-vframes', '1', '-q:v', '3', '-vf', 'scale=320:-1',
                str(thumbnail_path)
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # Se falhar, talvez o vídeo tenha menos de 5s, tenta no início
            try:
                command = [
                    'ffmpeg', '-i', str(video_path),
                    '-vframes', '1', '-q:v', '3', '-vf', 'scale=320:-1',
                    str(thumbnail_path)
                ]
                subprocess.run(command, check=True, capture_output=True, text=True)
            except Exception:
                raise HTTPException(status_code=500, detail="Falha ao gerar thumbnail")

    return FileResponse(thumbnail_path)


@router.get("/stream/{folder_name}/{filename}", tags=["Media"], summary="Serve um arquivo de vídeo")
def stream_video(folder_name: str, filename: str):
    """
    Serve um arquivo de vídeo para ser reproduzido no player do frontend.
    Determina o tipo de mídia (MIME type) dinamicamente a partir da extensão do arquivo.
    """
    video_path = VIDEOS_BASE_PATH / folder_name / filename
    
    # Imprime no console do backend o caminho que ele está tentando acessar.
    # Isso é EXTREMAMENTE útil para depuração!
    print(f"Tentando servir o vídeo: {video_path}")

    if not os.path.exists(video_path):
        print(f"ERRO: Arquivo não encontrado em {video_path}")
        raise HTTPException(status_code=404, detail=f"Vídeo não encontrado em {video_path}")
    
    # Determina o tipo de mídia (MIME type) dinamicamente
    media_type, _ = mimetypes.guess_type(video_path)
    if media_type is None:
        # Se não conseguir adivinhar, usa um padrão genérico
        media_type = "application/octet-stream"

    return FileResponse(video_path, media_type=media_type, headers={"Accept-Ranges": "bytes"})

# ==============================================================================
# --- ENDPOINTS DE PROCESSAMENTO E WEBSOCKET ---
# ==============================================================================

@router.post("/process/{folder_name}/{filename}", status_code=202, tags=["Processing"], summary="Inicia a análise de cenas")
async def process_video(folder_name: str, filename: str, background_tasks: BackgroundTasks):
    """
    Inicia o processo de detecção de cena para um vídeo em segundo plano.
    Retorna imediatamente um 'job_id' para o cliente se conectar via WebSocket.
    """
    video_path = str(VIDEOS_BASE_PATH / folder_name / filename)
    output_folder = str(VIDEOS_BASE_PATH / folder_name)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    job_id = str(uuid.uuid4())

    async def progress_callback(data: dict):
        await manager.send_json(job_id, data)

    background_tasks.add_task(
        run_scene_detection,
        video_path=video_path,
        output_folder=output_folder,
        callback=progress_callback
    )
    
    return {"job_id": job_id, "message": "Processamento iniciado"}


@router.websocket("/ws/progress/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    Endpoint WebSocket que o cliente usa para receber atualizações de progresso
    para um 'job_id' específico.
    """
    await manager.connect(job_id, websocket)
    try:
        while True:
            # Mantém a conexão viva esperando por mensagens (não esperamos nenhuma do cliente)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)

@router.get("/scenes/{folder_name}/{filename}", tags=["Scenes"], summary="Retorna os dados das cenas de um vídeo processado")
def get_scene_data(folder_name: str, filename: str):
    """
    Lê o arquivo _cenas.json e retorna seu conteúdo de forma segura,
    lidando com todos os tipos de erros de formatação ou conteúdo.
    """
    base_name, _ = os.path.splitext(filename)
    json_path = VIDEOS_BASE_PATH / folder_name / f"{base_name}_cenas.json"

    print(f"\n[DEBUG] Tentando buscar cenas para o arquivo: {json_path}")

    if not os.path.exists(json_path):
        print(f"[DEBUG] Arquivo de cenas não encontrado. Retornando vazio.")
        return {"scenes": [], "duration": 0}

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Se o arquivo estiver vazio, json.load() falha. Tratamos isso primeiro.
            if not content:
                print(f"[DEBUG] O arquivo JSON está vazio. Retornando vazio.")
                return {"scenes": [], "duration": 0}
            scene_data = json.loads(content)

    except json.JSONDecodeError:
        print(f"[DEBUG] ERRO: O arquivo JSON '{json_path}' está corrompido.")
        return {"scenes": [], "duration": 0}
    except Exception as e:
        print(f"[DEBUG] ERRO Inesperado ao ler o arquivo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao ler o arquivo: {e}")

    # --- LÓGICA DE VALIDAÇÃO DO CONTEÚDO ---
    if not isinstance(scene_data, list):
        print(f"[DEBUG] Aviso: O conteúdo do JSON não é uma lista. É do tipo {type(scene_data)}.")
        return {"scenes": [], "duration": 0}
        
    if not scene_data:
        print("[DEBUG] A lista de cenas no JSON está vazia.")
        return {"scenes": [], "duration": 0}
        
    # Filtra apenas as cenas válidas (que são dicionários com as chaves necessárias)
    valid_scenes = []
    for scene in scene_data:
        if isinstance(scene, dict) and 'start_time' in scene and 'end_time' in scene and 'duration' in scene:
            valid_scenes.append(scene)

    if not valid_scenes:
        print("[DEBUG] Nenhuma cena válida encontrada dentro da lista no JSON.")
        return {"scenes": [], "duration": 0}

    # Calcula a duração a partir da última cena válida
    total_duration = valid_scenes[-1]['end_time']
    
    print(f"[DEBUG] Sucesso! Encontradas {len(valid_scenes)} cenas válidas. Duração total: {total_duration}")
    return {"scenes": valid_scenes, "duration": total_duration}