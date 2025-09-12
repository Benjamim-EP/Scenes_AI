import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from app.core.schemas import SearchRequest
from pathlib import Path
import json
import os

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_FILE = BASE_DIR / "cenas_database.db"

def get_db():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

@router.post("/search", tags=["Search"], summary="Busca vídeos e retorna as cenas correspondentes")
def search_videos(request: SearchRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Busca vídeos que contêm cenas com critérios específicos e retorna os dados
    dessas cenas para navegação inteligente.
    """
    
    # --- Subquery para encontrar os scene_ids que correspondem ---
    subquery_conditions = []
    subquery_params = []
    
    if request.min_duration is not None and request.min_duration > 0:
        subquery_conditions.append("s.duration >= ?")
        subquery_params.append(request.min_duration)
    if request.max_duration is not None and request.max_duration > 0:
        subquery_conditions.append("s.duration <= ?")
        subquery_params.append(request.max_duration)
        
    if request.exclude_tags:
        for tag in request.exclude_tags:
            subquery_conditions.append(f"s.scene_id NOT IN (SELECT st.scene_id FROM scene_tags st JOIN tags t ON st.tag_id = t.tag_id WHERE t.tag_name = ?)")
            subquery_params.append(tag)
    
    subquery_where = " AND ".join(subquery_conditions) if subquery_conditions else "1=1"
    
    subquery_from_joins = "FROM scenes s"
    subquery_having = ""
    if request.include_tags:
        subquery_from_joins += " JOIN scene_tags st ON s.scene_id = st.scene_id JOIN tags t ON st.tag_id = t.tag_id"
        placeholders = ', '.join('?' for _ in request.include_tags)
        subquery_where += f" AND t.tag_name IN ({placeholders})"
        subquery_params.extend(request.include_tags)
        subquery_having = f"GROUP BY s.scene_id HAVING COUNT(DISTINCT t.tag_name) = ?"
        subquery_params.append(len(request.include_tags))

    # --- Query Principal para agrupar por vídeo e coletar cenas correspondentes ---
    query = f"""
    SELECT
        v.video_id,
        v.video_name,
        v.file_path,
        -- [MODIFICADO] Agrega um objeto JSON para cada cena correspondente
        json_group_array(
            json_object('scene_id', s_match.scene_id, 'start_time', s_match.start_time, 'end_time', s_match.end_time)
        ) as matching_scenes
    FROM videos v
    JOIN scenes s_match ON v.video_id = s_match.video_id
    WHERE s_match.scene_id IN (
        SELECT s.scene_id {subquery_from_joins} WHERE {subquery_where} {subquery_having}
    )
    GROUP BY v.video_id
    ORDER BY COUNT(s_match.scene_id) DESC -- Ordena por vídeos com mais cenas correspondentes
    LIMIT ? OFFSET ?
    """
    
    final_params = subquery_params + [request.limit, (request.page - 1) * request.limit]

    try:
        cursor = db.cursor()
        results = cursor.execute(query, final_params).fetchall()

        videos = []
        for row in results:
            video = dict(row)
            # Deserializa a string JSON das cenas
            video['matching_scenes'] = sorted(json.loads(video['matching_scenes']), key=lambda x: x['start_time'])
            
            path_obj = Path(video['file_path'])
            video['filename'] = path_obj.name
            video['folder'] = path_obj.parent.name
            video['has_scenes_json'] = True
            
            videos.append(video)
        
        return {"results": videos}
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {e}")