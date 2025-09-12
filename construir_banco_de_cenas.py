import os
import sqlite3
import json
from tqdm import tqdm

# ==============================================================================
# --- CONFIGURAÇÃO ---
# ==============================================================================

# 1. Pasta raiz onde estão as subpastas das categorias (atrizes/estúdios)
#    (Ex: 'backend/videos')
VIDEOS_ROOT_FOLDER = "backend/videos"

# 2. Nome e caminho do arquivo do banco de dados que será criado/atualizado
DB_FILE = "cenas_database.db"

# 3. Duração mínima (em segundos) que uma cena deve ter para ser catalogada
MIN_SCENE_DURATION = 2.0

# ==============================================================================
# --- FUNÇÕES AUXILIARES ---
# ==============================================================================

def setup_database(db_path):
    """
    Cria a estrutura de tabelas no banco de dados SQLite.
    Se o arquivo já existir, ele será usado; não será apagado.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        video_id INTEGER PRIMARY KEY,
        video_name TEXT NOT NULL UNIQUE,
        category TEXT,
        file_path TEXT
    )""")
    
    # [MODIFICADO] A coluna clip_path agora pode ser NULL
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scenes (
        scene_id INTEGER PRIMARY KEY,
        video_id INTEGER NOT NULL,
        scene_number INTEGER NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        duration REAL NOT NULL,
        clip_path TEXT, -- Será preenchido sob demanda
        FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
    )""")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS tags (tag_id INTEGER PRIMARY KEY, tag_name TEXT NOT NULL UNIQUE)")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scene_tags (
        scene_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        score REAL NOT NULL,
        PRIMARY KEY (scene_id, tag_id),
        FOREIGN KEY (scene_id) REFERENCES scenes(scene_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
    )""")
    
    conn.commit()
    print(f"Banco de dados '{db_path}' conectado e estrutura verificada.")
    return conn

# ==============================================================================
# --- FUNÇÃO PRINCIPAL ---
# ==============================================================================
def build_scene_database():
    """
    Função principal que varre as pastas, processa os JSONs e popula o
    banco de dados com informações de vídeos e cenas, SEM extrair os clipes.
    """
    conn = setup_database(DB_FILE)
    cursor = conn.cursor()

    try:
        category_folders = [d for d in os.listdir(VIDEOS_ROOT_FOLDER) if os.path.isdir(os.path.join(VIDEOS_ROOT_FOLDER, d)) and not d.startswith('.')]
    except FileNotFoundError:
        print(f"ERRO: A pasta raiz de vídeos '{VIDEOS_ROOT_FOLDER}' não foi encontrada.")
        return

    for category_name in tqdm(category_folders, desc="Processando Categorias"):
        category_folder_path = os.path.join(VIDEOS_ROOT_FOLDER, category_name)
        
        json_files = [f for f in os.listdir(category_folder_path) if f.endswith("_cenas.json")]

        for json_filename in tqdm(json_files, desc=f"  Vídeos de '{category_name}'", leave=False):
            base_video_name = json_filename.replace("_cenas.json", "")
            
            source_video_path = None
            for ext in ['.mp4', '.mkv', '.mov', '.webm', '.avi', '.wmv', '.mpg']:
                path_try = os.path.join(category_folder_path, f"{base_video_name}{ext}")
                if os.path.exists(path_try):
                    source_video_path = path_try
                    break
            
            if not source_video_path:
                tqdm.write(f"Aviso: Vídeo original para '{json_filename}' não encontrado. Pulando.")
                continue

            cursor.execute("INSERT OR IGNORE INTO videos (video_name, category, file_path) VALUES (?, ?, ?)", 
                           (base_video_name, category_name, source_video_path.replace(os.path.sep, '/')))
            cursor.execute("SELECT video_id FROM videos WHERE video_name = ?", (base_video_name,))
            video_id = cursor.fetchone()[0]
            
            json_path = os.path.join(category_folder_path, json_filename)
            with open(json_path, 'r', encoding='utf-8') as f:
                try: scenes_data = json.load(f)
                except json.JSONDecodeError: continue

            if not isinstance(scenes_data, list): continue

            for scene in scenes_data:
                scene_duration = scene.get('duration', 0)
                if scene_duration < MIN_SCENE_DURATION:
                    continue
                
                # Insere a cena no DB sem o clip_path
                cursor.execute("INSERT INTO scenes (video_id, scene_number, start_time, end_time, duration) VALUES (?, ?, ?, ?, ?)",
                               (video_id, scene.get('cena_n'), scene.get('start_time'), scene.get('end_time'), scene_duration))
                scene_id = cursor.lastrowid

                # Insere as tags e as relações
                for tag_name, score in scene.get('tags_principais', {}).items():
                    tag_name_std = tag_name.replace(' ', '_')
                    cursor.execute("INSERT OR IGNORE INTO tags (tag_name) VALUES (?)", (tag_name_std,))
                    cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name_std,))
                    tag_id = cursor.fetchone()[0]
                    cursor.execute("INSERT OR IGNORE INTO scene_tags (scene_id, tag_id, score) VALUES (?, ?, ?)",
                                   (scene_id, tag_id, score))

            # Salva as alterações no DB para este vídeo
            conn.commit()
    
    conn.close()
    print("\n--- Processo de catalogação do banco de dados concluído! ---")
    print("Nenhum clipe de vídeo foi extraído, apenas as informações foram salvas.")

# ==============================================================================
# --- EXECUÇÃO ---
# ==============================================================================
if __name__ == "__main__":
    build_scene_database()