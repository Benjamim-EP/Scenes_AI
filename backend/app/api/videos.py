import os
import shutil
import subprocess
import uuid
from pathlib import Path
import mimetypes
import json
import sqlite3

from fastapi import (APIRouter, BackgroundTasks, HTTPException, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import FileResponse

from app.core.websockets import manager
from app.services.processing_service import run_scene_detection
from app.core.schemas import ProcessRequest # Importe o novo modelo

# ==============================================================================
# --- CONFIGURAÇÃO DO ROTEADOR E CAMINHOS ---
# ==============================================================================
router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VIDEOS_BASE_PATH = BASE_DIR / "videos"
THUMBNAIL_CACHE_PATH = VIDEOS_BASE_PATH / ".thumbnails"

# [A CORREÇÃO ESTÁ AQUI] Definimos o caminho para o banco de dados neste arquivo também
DB_FILE = BASE_DIR.parent / "cenas_database.db"

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
            command = ['ffmpeg', '-ss', '5', '-i', str(video_path),'-vframes', '1', '-q:v', '3', '-vf', 'scale=320:-1',str(thumbnail_path)]
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            try:
                command = ['ffmpeg', '-i', str(video_path),'-vframes', '1', '-q:v', '3', '-vf', 'scale=320:-1',str(thumbnail_path)]
                subprocess.run(command, check=True, capture_output=True, text=True)
            except Exception:
                raise HTTPException(status_code=500, detail="Falha ao gerar thumbnail")

    return FileResponse(thumbnail_path)

@router.get("/stream/{folder_name}/{filename}", tags=["Media"], summary="Serve um arquivo de vídeo")
def stream_video(folder_name: str, filename: str):
    """
    Serve um arquivo de vídeo para ser reproduzido no player do frontend.
    """
    video_path = VIDEOS_BASE_PATH / folder_name / filename
    print(f"Tentando servir o vídeo: {video_path}")
    if not os.path.exists(video_path):
        print(f"ERRO: Arquivo não encontrado em {video_path}")
        raise HTTPException(status_code=404, detail=f"Vídeo não encontrado em {video_path}")
    media_type, _ = mimetypes.guess_type(video_path)
    if media_type is None:
        media_type = "application/octet-stream"
    return FileResponse(video_path, media_type=media_type, headers={"Accept-Ranges": "bytes"})

# ==============================================================================
# --- ENDPOINTS DE PROCESSAMENTO E WEBSOCKET ---
# ==============================================================================

@router.post("/process/{folder_name}/{filename}", status_code=202, tags=["Processing"], summary="Inicia a análise de cenas")
async def process_video(
    folder_name: str, 
    filename: str, 
    # [MODIFICADO] Recebe os parâmetros do corpo da requisição
    params: ProcessRequest, 
    background_tasks: BackgroundTasks
):
    """
    Inicia o processo de detecção de cena com parâmetros customizados.
    """
    video_path = str(VIDEOS_BASE_PATH / folder_name / filename)
    output_folder = str(VIDEOS_BASE_PATH / folder_name)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    job_id = str(uuid.uuid4())

    async def progress_callback(data: dict):
        await manager.send_json(job_id, data)

    # [MODIFICADO] Passa os parâmetros recebidos para a função de processamento
    background_tasks.add_task(
        run_scene_detection,
        video_path=video_path,
        output_folder=output_folder,
        callback=progress_callback,
        fps=params.fps,
        limiar_similaridade=params.similarity_threshold,
        batch_size=params.batch_size
    )
    
    return {"job_id": job_id, "message": "Processamento iniciado com parâmetros customizados"}

# ==============================================================================
# --- ENDPOINT DE DADOS DE CENAS (CORRIGIDO) ---
# ==============================================================================

@router.get("/scenes/{folder_name}/{filename}", tags=["Scenes"], summary="Retorna os dados das cenas de um vídeo processado")
def get_scene_data(folder_name: str, filename: str):
    """
    Lê o arquivo _cenas.json e o enriquece com os scene_ids do banco de dados.
    """
    base_name, _ = os.path.splitext(filename)
    json_path = VIDEOS_BASE_PATH / folder_name / f"{base_name}_cenas.json"

    print(f"\n[DEBUG] Tentando buscar cenas para o arquivo: {json_path}")

    if not os.path.exists(json_path):
        print("[DEBUG] Arquivo de cenas não encontrado. Retornando vazio.")
        return {"scenes": [], "duration": 0}

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content:
                print("[DEBUG] O arquivo JSON está vazio. Retornando vazio.")
                return {"scenes": [], "duration": 0}
            scene_data_from_json = json.loads(content)

        if not isinstance(scene_data_from_json, list) or not scene_data_from_json:
            print(f"[DEBUG] Conteúdo do JSON não é uma lista válida.")
            return {"scenes": [], "duration": 0}

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT video_id FROM videos WHERE video_name = ?", (base_name,))
        video_row = cursor.fetchone()
        if not video_row:
            conn.close()
            print(f"[DEBUG] Vídeo '{base_name}' não encontrado no banco de dados.")
            return {"scenes": [], "duration": 0}
        video_id = video_row['video_id']

        cursor.execute("SELECT scene_id, scene_number FROM scenes WHERE video_id = ?", (video_id,))
        scenes_from_db = {row['scene_number']: row['scene_id'] for row in cursor.fetchall()}
        conn.close()

        enriched_scenes = []
        for scene in scene_data_from_json:
            scene_num = scene.get('cena_n') or scene.get('scene_number')
            if scene_num in scenes_from_db:
                scene['scene_id'] = scenes_from_db[scene_num]
                enriched_scenes.append(scene)

        if not enriched_scenes:
            print("[DEBUG] Nenhuma cena do JSON correspondeu às cenas no DB.")
            return {"scenes": [], "duration": 0}
            
        total_duration = enriched_scenes[-1]['end_time']
        
        print(f"[DEBUG] Sucesso! Encontradas {len(enriched_scenes)} cenas. Duração: {total_duration}")
        return {"scenes": enriched_scenes, "duration": total_duration}

    except json.JSONDecodeError:
        print(f"[DEBUG] ERRO: O arquivo JSON '{json_path}' está corrompido.")
        return {"scenes": [], "duration": 0}
    except Exception as e:
        print(f"[DEBUG] ERRO Inesperado ao processar: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar dados das cenas: {e}")