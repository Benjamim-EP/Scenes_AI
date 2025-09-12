import os
import sqlite3
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from pathlib import Path

# ==============================================================================
# --- CONFIGURAÇÃO E DEPENDÊNCIAS ---
# ==============================================================================
router = APIRouter()

# Define os caminhos base para o banco de dados e a pasta de vídeos
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_FILE = BASE_DIR / "cenas_database.db"
VIDEOS_ROOT_FOLDER = BASE_DIR / "backend" / "videos"

# Modelo Pydantic para validar o corpo das requisições POST
class PathList(BaseModel):
    paths: List[str]

def get_db():
    """Função de dependência do FastAPI para obter uma conexão com o banco de dados."""
    if not DB_FILE.exists():
        raise HTTPException(status_code=503, detail=f"Arquivo de banco de dados não encontrado em {DB_FILE}")
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

# ==============================================================================
# --- ENDPOINTS DA API DE GERENCIAMENTO ---
# ==============================================================================

@router.get("/management/status", tags=["Management"], summary="Verifica a sincronia entre o DB e o sistema de arquivos")
def get_sync_status(db: sqlite3.Connection = Depends(get_db)):
    """
    Compara os vídeos no banco de dados com os arquivos de vídeo reais
    e retorna um relatório de status com órfãos e arquivos não catalogados.
    """
    try:
        cursor = db.cursor()
        cursor.execute("SELECT file_path FROM videos")
        db_paths = {row['file_path'] for row in cursor.fetchall()}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")

    filesystem_paths = set()
    supported_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm', '.mpg', '.wmv')
    
    if not VIDEOS_ROOT_FOLDER.exists():
        raise HTTPException(status_code=404, detail=f"Pasta raiz de vídeos '{VIDEOS_ROOT_FOLDER}' não encontrada.")

    for root, _, files in os.walk(VIDEOS_ROOT_FOLDER):
        for file in files:
            if file.lower().endswith(supported_extensions):
                full_path = Path(root) / file
                relative_path = os.path.relpath(full_path, BASE_DIR).replace(os.path.sep, '/')
                filesystem_paths.add(relative_path)

    orphan_records = sorted(list(db_paths - filesystem_paths))
    untracked_files = sorted(list(filesystem_paths - db_paths))
    
    return {
        "db_video_count": len(db_paths),
        "filesystem_video_count": len(filesystem_paths),
        "orphan_records": orphan_records,
        "untracked_files": untracked_files
    }

@router.post("/management/cleanup", tags=["Management"], summary="Remove registros órfãos do DB")
def cleanup_orphan_records(payload: PathList, db: sqlite3.Connection = Depends(get_db)):
    """
    Recebe uma lista de file_paths e os remove da tabela 'videos'.
    O ON DELETE CASCADE cuidará de remover as cenas e tags associadas.
    """
    if not payload.paths:
        return {"message": "Nenhum caminho fornecido para limpeza.", "deleted_count": 0}
            
    cursor = db.cursor()
    deleted_count = 0
    try:
        for path in payload.paths:
            cursor.execute("DELETE FROM videos WHERE file_path = ?", (path,))
            deleted_count += cursor.rowcount
        db.commit()
        return {"message": "Limpeza concluída com sucesso.", "deleted_count": deleted_count}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados durante a limpeza: {e}")

@router.post("/management/scan_new", tags=["Management"], summary="Adiciona novos vídeos ao DB")
def scan_new_videos(payload: PathList, db: sqlite3.Connection = Depends(get_db)):
    """
    Recebe uma lista de file_paths de vídeos não catalogados e os adiciona ao DB,
    assumindo que seus arquivos _cenas.json já existem.
    """
    if not payload.paths:
        return {"message": "Nenhum caminho fornecido para escanear.", "added_count": 0}

    cursor = db.cursor()
    added_count = 0
    
    for relative_path_str in payload.paths:
        try:
            # Reconstrói o caminho completo a partir do caminho relativo
            video_path = BASE_DIR / relative_path_str
            base_video_name = video_path.stem
            category_name = video_path.parent.name
            
            json_path = video_path.with_name(f"{base_video_name}_cenas.json")

            if not json_path.exists():
                print(f"Aviso: JSON para '{video_path.name}' não encontrado. Pulando.")
                continue

            # Insere o vídeo
            cursor.execute("INSERT OR IGNORE INTO videos (video_name, category, file_path) VALUES (?, ?, ?)",
                           (base_video_name, category_name, relative_path_str))
            cursor.execute("SELECT video_id FROM videos WHERE file_path = ?", (relative_path_str,))
            video_id_result = cursor.fetchone()
            if not video_id_result: continue
            video_id = video_id_result['video_id']
            
            # Insere as cenas e tags
            with open(json_path, 'r', encoding='utf-8') as f:
                scenes_data = json.load(f)
            
            if not isinstance(scenes_data, list): continue

            for scene in scenes_data:
                # Usa INSERT OR IGNORE para evitar duplicatas se o script for rodado novamente
                cursor.execute("INSERT OR IGNORE INTO scenes (video_id, scene_number, start_time, end_time, duration) VALUES (?, ?, ?, ?, ?)",
                               (video_id, scene.get('cena_n'), scene.get('start_time'), scene.get('end_time'), scene.get('duration')))
                
                # Para obter o scene_id, precisamos buscá-lo, já que o IGNORE não retorna lastrowid
                cursor.execute("SELECT scene_id FROM scenes WHERE video_id = ? AND scene_number = ?", (video_id, scene.get('cena_n')))
                scene_id_result = cursor.fetchone()
                if not scene_id_result: continue
                scene_id = scene_id_result['scene_id']

                for tag_name, score in scene.get('tags_principais', {}).items():
                    tag_name_std = tag_name.replace(' ', '_')
                    cursor.execute("INSERT OR IGNORE INTO tags (tag_name) VALUES (?)", (tag_name_std,))
                    cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name_std,))
                    tag_id_result = cursor.fetchone()
                    if tag_id_result:
                        tag_id = tag_id_result[0]
                        cursor.execute("INSERT OR IGNORE INTO scene_tags (scene_id, tag_id, score) VALUES (?, ?, ?)",
                                       (scene_id, tag_id, score))
            added_count += 1
        except Exception as e:
            print(f"Erro ao adicionar o vídeo '{relative_path_str}': {e}")
            continue
            
    db.commit()
    return {"message": f"{added_count} de {len(payload.paths)} novos vídeos foram adicionados com sucesso.", "added_count": added_count}