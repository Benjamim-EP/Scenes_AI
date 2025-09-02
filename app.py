import eel
import sqlite3
import os
import json
import shlex # Biblioteca para parsing de strings de busca
from urllib.parse import quote

# ==============================================================================
# --- CONFIGURAÇÃO ---
# ==============================================================================
DB_FILE = "cenas_database.db"
PAGE_SIZE = 20
TAGS_FILE = "tags.txt"

ALLOWED_TAGS = set()
def load_allowed_tags():
    """Lê o arquivo tags.txt e o carrega em um set para busca rápida."""
    global ALLOWED_TAGS
    if not os.path.exists(TAGS_FILE):
        print(f"AVISO: '{TAGS_FILE}' não encontrado. Todas as tags serão exibidas.")
        return
        
    try:
        with open(TAGS_FILE, 'r', encoding='utf-8') as f:
            ALLOWED_TAGS = {line.strip() for line in f if line.strip()}
        print(f"Carregadas {len(ALLOWED_TAGS)} tags permitidas de '{TAGS_FILE}'.")
    except Exception as e:
        print(f"ERRO ao ler '{TAGS_FILE}': {e}")

# ==============================================================================
# --- FUNÇÕES EXPOSTAS PARA O JAVASCRIPT ---
# ==============================================================================

@eel.expose
def get_all_actresses():
    """Busca uma lista única de todas as atrizes no banco de dados para a tela inicial."""
    if not os.path.exists(DB_FILE): return []
    conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    query = "SELECT actress, file_path FROM videos WHERE actress IS NOT NULL AND actress != '' GROUP BY actress ORDER BY actress"
    cursor.execute(query)
    actresses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for actress in actresses:
        if actress['file_path']:
            actress['file_path'] = quote(actress['file_path'].replace(os.path.sep, '/'))
    return actresses

@eel.expose
def get_videos_page(actress_name, page_number=1):
    conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE actress = ?", (actress_name,))
    total_videos = cursor.fetchone()[0]
    total_pages = (total_videos + PAGE_SIZE - 1) // PAGE_SIZE; offset = (page_number - 1) * PAGE_SIZE
    
    # [CORRIGIDO] Removido o DISTINCT de dentro do GROUP_CONCAT.
    # A subquery 'top_tags' já garante a unicidade.
    query = """
    SELECT v.video_id, v.video_name, v.file_path,
           (SELECT GROUP_CONCAT(t.tag_name || ':' || printf("%.2f", top_tags.avg_score), '|||')
            FROM (
                SELECT st.tag_id, AVG(st.score) as avg_score
                FROM scenes s JOIN scene_tags st ON s.scene_id = st.scene_id
                WHERE s.video_id = v.video_id GROUP BY st.tag_id ORDER BY avg_score DESC
            ) AS top_tags JOIN tags t ON top_tags.tag_id = t.tag_id
           ) AS all_tags_with_scores
    FROM videos v WHERE v.actress = ? ORDER BY v.video_name LIMIT ? OFFSET ?
    """
    cursor.execute(query, (actress_name, PAGE_SIZE, offset)); videos_raw = [dict(row) for row in cursor.fetchall()]; conn.close()
    
    for video in videos_raw:
        # ... (resto da função sem alterações)
        video['main_tags'] = video.pop('all_tags_with_scores')
        if video['main_tags'] and ALLOWED_TAGS:
            video_tags_with_scores = video['main_tags'].split('|||')
            filtered_tags = [item for item in video_tags_with_scores if item.split(':')[0] in ALLOWED_TAGS]
            video['main_tags'] = "|||".join(filtered_tags)
        if video['file_path']: video['file_path'] = quote(video['file_path'].replace(os.path.sep, '/'))
    
    return { "videos": videos_raw, "currentPage": page_number, "totalPages": total_pages }

@eel.expose
def search_videos_by_tags(actress_name, search_query, page_number=1): # [MODIFICADO] Adiciona page_number
    """
    Busca vídeos de forma paginada para otimizar o uso de memória.
    """
    conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()

    try: tokens = shlex.split(search_query.lower().strip())
    except ValueError: tokens = search_query.lower().strip().split()
    
    positive_tags = [token for token in tokens if not token.startswith('-')]
    negative_tags = [token.strip('-') for token in tokens if token.startswith('-')]

    if not positive_tags:
        return {"videos": [], "search_query": search_query, "totalPages": 0}

    main_search_tag = positive_tags[0]
    
    # --- Parte 1: Construir a subquery para obter TODOS os IDs de vídeo correspondentes ---
    id_query = "SELECT v.video_id FROM videos v"
    params_id = []

    # JOINs necessários apenas para a filtragem
    if positive_tags or negative_tags:
        id_query += " JOIN scenes s ON v.video_id = s.video_id JOIN scene_tags st ON s.scene_id = st.scene_id JOIN tags t ON st.tag_id = t.tag_id"
    
    id_query += " WHERE v.actress = ?"
    params_id.append(actress_name)
    
    # Agrupamento para filtros
    if positive_tags:
        id_query += f" GROUP BY v.video_id HAVING "
        id_query += " AND ".join([f"SUM(CASE WHEN t.tag_name = ? THEN 1 ELSE 0 END) > 0" for tag in positive_tags])
        params_id.extend(positive_tags)
    
    if negative_tags:
        id_query += " AND " if positive_tags else " GROUP BY v.video_id HAVING "
        id_query += " AND ".join([f"SUM(CASE WHEN t.tag_name = ? THEN 1 ELSE 0 END) = 0" for tag in negative_tags])
        params_id.extend(negative_tags)
        
    # --- Parte 2: Executar a query de IDs e contar o total ---
    cursor.execute(id_query, params_id)
    matching_video_ids = [row['video_id'] for row in cursor.fetchall()]
    
    if not matching_video_ids:
        conn.close()
        return {"videos": [], "search_query": search_query, "totalPages": 0, "currentPage": 1}
        
    total_videos = len(matching_video_ids)
    total_pages = (total_videos + PAGE_SIZE - 1) // PAGE_SIZE
    offset = (page_number - 1) * PAGE_SIZE
    
    # Pega apenas os IDs para a página atual
    paged_ids = matching_video_ids[offset : offset + PAGE_SIZE]
    if not paged_ids:
        conn.close()
        return {"videos": [], "search_query": search_query, "totalPages": total_pages, "currentPage": page_number}

    # --- Parte 3: Buscar os dados completos APENAS para os vídeos da página atual ---
    final_query = f"""
    SELECT v.video_id, v.video_name, v.file_path,
           (SELECT AVG(st.score) FROM scenes s JOIN scene_tags st ON s.scene_id = st.scene_id JOIN tags t ON st.tag_id = t.tag_id WHERE s.video_id = v.video_id AND t.tag_name = ?) as relevance_score,
           (SELECT GROUP_CONCAT(t.tag_name || ':' || printf("%.2f", top_tags.avg_score), '|||')
            FROM (SELECT st.tag_id, AVG(st.score) as avg_score FROM scenes s JOIN scene_tags st ON s.scene_id = st.scene_id WHERE s.video_id = v.video_id GROUP BY st.tag_id ORDER BY avg_score DESC) AS top_tags
            JOIN tags t ON top_tags.tag_id = t.tag_id) AS all_tags_with_scores
    FROM videos v
    WHERE v.video_id IN ({','.join(['?'] * len(paged_ids))})
    """
    
    params_final = [main_search_tag] + paged_ids
    cursor.execute(final_query, params_final)
    videos_raw = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Ordena os resultados em Python com base na relevância
    videos_raw.sort(key=lambda x: x.get('relevance_score') or 0, reverse=True)

    # ... (resto do processamento de tags e caminhos) ...
    for video in videos_raw:
        video['main_tags'] = video.pop('all_tags_with_scores')
        if video['main_tags'] and ALLOWED_TAGS:
            video_tags_with_scores = video['main_tags'].split('|||')
            filtered_tags = [item for item in video_tags_with_scores if item.split(':')[0] in ALLOWED_TAGS]
            video['main_tags'] = "|||".join(filtered_tags)
        if video['file_path']:
            video['file_path'] = quote(video['file_path'].replace(os.path.sep, '/'))

    return {"videos": videos_raw, "search_query": search_query, "highlight_tag": main_search_tag, "currentPage": page_number, "totalPages": total_pages}

@eel.expose
def get_scenes_for_video(video_id):
    """Busca as cenas e suas tags para um vídeo específico."""
    conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    query = """
    SELECT s.scene_id, s.start_time, s.end_time, GROUP_CONCAT(t.tag_name) as tags
    FROM scenes s
    LEFT JOIN scene_tags st ON s.scene_id = st.scene_id
    LEFT JOIN tags t ON st.tag_id = t.tag_id
    WHERE s.video_id = ?
    GROUP BY s.scene_id ORDER BY s.start_time
    """
    cursor.execute(query, (video_id,)); scenes = [dict(row) for row in cursor.fetchall()]; conn.close()
    return scenes

@eel.expose
def get_all_tags_for_autocomplete():
    """Retorna a lista de tags permitidas para o autocomplete."""
    return json.dumps(sorted(list(ALLOWED_TAGS)))

# ==============================================================================
# --- INICIALIZAÇÃO DA APLICAÇÃO ---
# ==============================================================================
if __name__ == "__main__":
    load_allowed_tags()
    
    eel.init('web')
    
    print("Iniciando 'Pulser Edits'...")
    
    try:
        eel.start('home.html', size=(1400, 900))
    except Exception as e:
        print(f"ERRO ao iniciar o Eel. Verifique se o Chrome/Edge está instalado. Erro: {e}")