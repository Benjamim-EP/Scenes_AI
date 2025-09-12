import sqlite3
import json
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = BASE_DIR.parent / "cenas_database.db"

def add_video_to_database(video_path_str: str, category_name: str, scenes_data: list):
    """
    Adiciona um único vídeo e suas cenas ao banco de dados.
    Esta é uma versão focada de 'construir_banco_de_cenas.py'.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    base_video_name = Path(video_path_str).stem
    
    try:
        # Garante que o vídeo está na tabela 'videos'
        cursor.execute("INSERT OR IGNORE INTO videos (video_name, category, file_path) VALUES (?, ?, ?)",
                       (base_video_name, category_name, video_path_str.replace(os.path.sep, '/')))
        
        cursor.execute("SELECT video_id FROM videos WHERE video_name = ?", (base_video_name,))
        video_id_result = cursor.fetchone()
        if not video_id_result:
            raise Exception(f"Não foi possível encontrar ou criar o vídeo '{base_video_name}' no DB.")
        video_id = video_id_result[0]

        # Remove cenas antigas deste vídeo para evitar duplicatas ao reprocessar
        cursor.execute("DELETE FROM scenes WHERE video_id = ?", (video_id,))

        # Insere as novas cenas e tags
        for scene in scenes_data:
            cursor.execute("INSERT INTO scenes (video_id, scene_number, start_time, end_time, duration) VALUES (?, ?, ?, ?, ?)",
                           (video_id, scene.get('cena_n'), scene.get('start_time'), scene.get('end_time'), scene.get('duration')))
            scene_id = cursor.lastrowid

            for tag_name, score in scene.get('tags_principais', {}).items():
                tag_name_std = tag_name.replace(' ', '_')
                cursor.execute("INSERT OR IGNORE INTO tags (tag_name) VALUES (?)", (tag_name_std,))
                cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name_std,))
                tag_id_result = cursor.fetchone()
                if tag_id_result:
                    tag_id = tag_id_result[0]
                    cursor.execute("INSERT OR IGNORE INTO scene_tags (scene_id, tag_id, score) VALUES (?, ?, ?)",
                                   (scene_id, tag_id, score))
        
        conn.commit()
        print(f"Vídeo '{base_video_name}' e suas {len(scenes_data)} cenas foram adicionados/atualizados no banco de dados.")

    except sqlite3.Error as e:
        print(f"Erro de banco de dados ao adicionar vídeo '{base_video_name}': {e}")
        conn.rollback()
    finally:
        conn.close()