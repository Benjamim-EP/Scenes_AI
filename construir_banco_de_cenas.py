import os
import sqlite3
import json
from tqdm import tqdm

# ==============================================================================
# --- CONFIGURAÇÃO ---
# ==============================================================================
DATA_ROOT_FOLDER = os.path.join("web", "videos")
DB_FILE = "cenas_database.db"

# ==============================================================================
# --- FUNÇÕES ---
# ==============================================================================
def setup_database(db_path):
    if os.path.exists(db_path): os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("CREATE TABLE videos (video_id INTEGER PRIMARY KEY, video_name TEXT NOT NULL UNIQUE, actress TEXT, file_path TEXT)")
    cursor.execute("CREATE TABLE scenes (scene_id INTEGER PRIMARY KEY, video_id INTEGER NOT NULL, scene_number INTEGER NOT NULL, start_time REAL NOT NULL, end_time REAL NOT NULL, duration REAL NOT NULL, FOREIGN KEY (video_id) REFERENCES videos(video_id))")
    cursor.execute("CREATE TABLE tags (tag_id INTEGER PRIMARY KEY, tag_name TEXT NOT NULL UNIQUE)")
    cursor.execute("CREATE TABLE scene_tags (scene_id INTEGER NOT NULL, tag_id INTEGER NOT NULL, score REAL NOT NULL, PRIMARY KEY (scene_id, tag_id), FOREIGN KEY (scene_id) REFERENCES scenes(scene_id) ON DELETE CASCADE, FOREIGN KEY (tag_id) REFERENCES tags(tag_id))")
    conn.commit()
    print("Nova estrutura de banco de dados criada.")
    return conn

def build_scene_database():
    conn = setup_database(DB_FILE)
    cursor = conn.cursor()

    try:
        actress_folders = [d for d in os.listdir(DATA_ROOT_FOLDER) if os.path.isdir(os.path.join(DATA_ROOT_FOLDER, d))]
    except FileNotFoundError:
        print(f"ERRO: A pasta '{DATA_ROOT_FOLDER}' não foi encontrada.")
        return

    video_extensions = ('.mp4', '.mkv', '.mov', '.webm', '.avi', '.wmv', '.mpg')

    for actress_name in tqdm(actress_folders, desc="Processando Atrizes"):
        actress_folder_path = os.path.join(DATA_ROOT_FOLDER, actress_name)
        video_files = [f for f in os.listdir(actress_folder_path) if f.lower().endswith(video_extensions)]

        for video_filename in tqdm(video_files, desc=f"  Vídeos de {actress_name}", leave=False):
            base_video_name, _ = os.path.splitext(video_filename)
            json_filename = f"{base_video_name}_cenas.json"
            json_path = os.path.join(actress_folder_path, json_filename)
            if not os.path.exists(json_path):
                continue

            path_to_save_in_db = os.path.join("videos", actress_name, video_filename).replace(os.path.sep, '/')
            cursor.execute("INSERT OR IGNORE INTO videos (video_name, actress, file_path) VALUES (?, ?, ?)", 
                           (base_video_name, actress_name, path_to_save_in_db))
            
            cursor.execute("SELECT video_id FROM videos WHERE video_name = ?", (base_video_name,))
            video_id = cursor.fetchone()[0]
            
            with open(json_path, 'r', encoding='utf-8') as f:
                try: scenes_data = json.load(f)
                except json.JSONDecodeError: continue

            for scene in scenes_data:
                cursor.execute("INSERT INTO scenes (video_id, scene_number, start_time, end_time, duration) VALUES (?, ?, ?, ?, ?)", (video_id, scene.get('cena_n'), scene.get('start_time'), scene.get('end_time'), scene.get('duration')))
                scene_id = cursor.lastrowid
                for tag_name_original, score in scene.get('tags_principais', {}).items():
                    
                    # [CORREÇÃO CRUCIAL] Padroniza a tag aqui!
                    tag_name_standardized = tag_name_original.replace(' ', '_')

                    cursor.execute("INSERT OR IGNORE INTO tags (tag_name) VALUES (?)", (tag_name_standardized,))
                    cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name_standardized,))
                    tag_id_result = cursor.fetchone()
                    if tag_id_result:
                        tag_id = tag_id_result[0]
                        cursor.execute("INSERT INTO scene_tags (scene_id, tag_id, score) VALUES (?, ?, ?)", (scene_id, tag_id, score))
    
    conn.commit()
    conn.close()
    print("\nBanco de dados reconstruído com tags padronizadas (espaços -> '_').")

if __name__ == "__main__":
    build_scene_database()