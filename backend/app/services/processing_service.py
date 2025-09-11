import os
import subprocess
import shutil
import huggingface_hub
import numpy as np
import onnxruntime as rt
import pandas as pd
from PIL import Image
import json
import re
import torch
import asyncio

# ==============================================================================
# SEÇÃO 1: CONSTANTES E CONFIGURAÇÕES DO MODELO
# ==============================================================================
MODEL_REPO = "SmilingWolf/wd-swinv2-tagger-v3"
GENERAL_THRESHOLD = 0.35
CHARACTER_THRESHOLD = 0.85
BATCH_SIZE = 4 # Tamanho de lote padrão, pode ser sobrescrito

# ==============================================================================
# SEÇÃO 2: CLASSE E FUNÇÕES AUXILIARES DE MACHINE LEARNING
# ==============================================================================

# (Estas são as funções do seu script do Colab, praticamente inalteradas)
kaomojis = ["0_0", "(o)_(o)", "+_+", "+_-", "._.", "<o>_<o>", "<|>_<|>", "=_=", ">_<", "3_3", "6_9", ">_o", "@_@", "^_^", "o_o", "u_u", "x_x", "|_|", "||_||"]

def load_labels(dataframe):
    name_series = dataframe["name"].map(lambda x: x.replace("_", " ") if x not in kaomojis else x)
    return name_series.tolist(), list(np.where(dataframe["category"] == 9)[0]), list(np.where(dataframe["category"] == 0)[0]), list(np.where(dataframe["category"] == 4)[0])

class Predictor:
    def __init__(self):
        self.model = None
        self.tag_names = None
        self.rating_indexes = None
        self.general_indexes = None
        self.character_indexes = None
        self.model_target_size = None
        self.last_loaded_repo = None

    def load_model(self, model_repo=MODEL_REPO):
        if self.last_loaded_repo == model_repo: return
        
        csv_path = huggingface_hub.hf_hub_download(model_repo, "selected_tags.csv")
        model_path = huggingface_hub.hf_hub_download(model_repo, "model.onnx")
        
        self.tag_names, self.rating_indexes, self.general_indexes, self.character_indexes = load_labels(pd.read_csv(csv_path))
        providers = ['CUDAExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider']
        self.model = rt.InferenceSession(model_path, providers=providers)
        _, height, _, _ = self.model.get_inputs()[0].shape
        self.model_target_size = height
        self.last_loaded_repo = model_repo

    def prepare_image(self, image):
        image = image.convert("RGB")
        max_dim = max(image.size)
        padded_image = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
        padded_image.paste(image, ((max_dim - image.size[0]) // 2, (max_dim - image.size[1]) // 2))
        if max_dim != self.model_target_size:
            padded_image = padded_image.resize((self.model_target_size, self.model_target_size), Image.BICUBIC)
        image_array = np.asarray(padded_image, dtype=np.float32)[:, :, ::-1]
        return np.expand_dims(image_array, axis=0)

    def predict_batch(self, images, general_thresh, character_thresh):
        batch_array = np.vstack([self.prepare_image(img) for img in images])
        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        preds_batch = self.model.run([label_name], {input_name: batch_array})[0]
        batch_results = []
        for preds in preds_batch:
            labels = list(zip(self.tag_names, preds.astype(float)))
            general_names = [labels[i] for i in self.general_indexes]
            character_names = [labels[i] for i in self.character_indexes]
            general_res = {x[0]: float(x[1]) for x in general_names if x[1] > general_thresh}
            character_res = {x[0]: float(x[1]) for x in character_names if x[1] > character_thresh}
            batch_results.append({**general_res, **character_res})
        return batch_results

# ==============================================================================
# SEÇÃO 3: FUNÇÕES DO PIPELINE DE PROCESSAMENTO (ADAPTADAS COM CALLBACK)
# ==============================================================================

# [MODIFICADO] A função extrair_frames agora é síncrona
def extrair_frames(caminho_video, diretorio_saida, fps):
    os.makedirs(diretorio_saida, exist_ok=True)
    caminho_saida_frames = os.path.join(diretorio_saida, 'frame_%06d.png')
    comando = ['ffmpeg', '-i', caminho_video, '-vf', f'fps={fps}', '-hide_banner', '-loglevel', 'error', caminho_saida_frames]
    
    # Usando o subprocess.run síncrono e confiável
    result = subprocess.run(comando, capture_output=True, text=True)

    if result.returncode != 0:
        # Imprime o erro do ffmpeg para ajudar na depuração
        print("Erro no FFmpeg (extrair_frames):", result.stderr)
        raise Exception(f"Falha na extração de frames. FFmpeg stderr: {result.stderr}")
    
    return len([f for f in os.listdir(diretorio_saida) if f.endswith('.png')])


async def gerar_tags_para_frames(predictor, pasta_frames, total_frames, batch_size, callback):
    results = {}
    img_files = sorted([f for f in os.listdir(pasta_frames) if f.lower().endswith('.png')])

    for i in range(0, len(img_files), batch_size):
        batch_file_names = img_files[i:i + batch_size]
        batch_images = [Image.open(os.path.join(pasta_frames, f)) for f in batch_file_names]
        
        batch_tags = predictor.predict_batch(batch_images, GENERAL_THRESHOLD, CHARACTER_THRESHOLD)
        
        for file_name, tags in zip(batch_file_names, batch_tags):
            results[file_name] = tags
        
        progress_percent = int(((i + len(batch_file_names)) / total_frames) * 100)
        overall_progress = 10 + int(0.7 * progress_percent) 
        await callback({"status": "processing", "progress": overall_progress, "message": f"Tagging frames ({progress_percent}%)"})

    return results

def detectar_trocas_de_cena(dados_tags, fps, limiar_similaridade):
    def calcular_similaridade_jaccard(tags1, tags2):
        set1, set2 = set(tags1.keys()), set(tags2.keys())
        intersecao = set1.intersection(set2)
        uniao = set1.union(set2)
        return len(intersecao) / len(uniao) if uniao else 1.0

    frames_ordenados = sorted(dados_tags.keys(), key=lambda x: int(re.search(r'(\d+)', x).group(1)))
    trocas_de_cena = [0.0]
    for i in range(len(frames_ordenados) - 1):
        similaridade = calcular_similaridade_jaccard(dados_tags[frames_ordenados[i]], dados_tags[frames_ordenados[i+1]])
        if similaridade < limiar_similaridade:
            trocas_de_cena.append((i + 1) / fps)
    return trocas_de_cena, frames_ordenados

def agrupar_cenas_com_tags(trocas_de_cena, frames_ordenados, dados_tags, fps, video_duration):
    cenas_agrupadas = []
    trocas_de_cena.append(video_duration)
    for i in range(len(trocas_de_cena) - 1):
        start_time, end_time = trocas_de_cena[i], trocas_de_cena[i+1]
        start_frame_idx = int(start_time * fps)
        end_frame_idx = int(end_time * fps)
        frames_da_cena = frames_ordenados[start_frame_idx:end_frame_idx]
        tags_agregadas = {}
        for frame_nome in frames_da_cena:
            for tag, score in dados_tags.get(frame_nome, {}).items():
                tags_agregadas.setdefault(tag, []).append(score)
        tags_medias = {tag: np.mean(scores) for tag, scores in tags_agregadas.items()}
        tags_principais = sorted(tags_medias.items(), key=lambda item: item[1], reverse=True)
        cenas_agrupadas.append({
            "cena_n": i + 1, "start_time": round(start_time, 3), "end_time": round(end_time, 3),
            "duration": round(end_time - start_time, 3),
            "tags_principais": {tag: round(score, 3) for tag, score in tags_principais}
        })
    return cenas_agrupadas

# ==============================================================================
# SEÇÃO 4: FUNÇÃO ORQUESTRADORA PRINCIPAL
# ==============================================================================

# Instância única do predictor para evitar recarregar o modelo
predictor = Predictor()

async def run_scene_detection(video_path: str, output_folder: str, callback,
                              fps: float = 1.0, limiar_similaridade: float = 0.4, batch_size: int = BATCH_SIZE):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    # Usa uma pasta temporária na raiz do backend
    temp_frames_path = os.path.join("temp_processing", f"temp_{base_name}_{os.getpid()}")
    os.makedirs(temp_frames_path, exist_ok=True)
    
    try:
        if predictor.model is None:
            await callback({"status": "processing", "progress": 0, "message": "Carregando modelo de IA..."})
            predictor.load_model()

        # 1. Extrair Frames (chamada síncrona)
        await callback({"status": "processing", "progress": 5, "message": f"Extraindo frames a {fps} FPS..."})
        num_frames = extrair_frames(video_path, temp_frames_path, fps) # Não precisa mais de await
        if num_frames == 0:
            raise Exception("Nenhum frame foi extraído do vídeo.")

        # 2. Gerar Tags (ainda async por causa do callback)
        await callback({"status": "processing", "progress": 10, "message": "Iniciando tagging de frames..."})
        dados_tags = await gerar_tags_para_frames(predictor, temp_frames_path, num_frames, batch_size, callback)
        if not dados_tags:
            raise Exception("Falha ao gerar tags para os frames.")

        # 3. Obter duração do vídeo (chamada síncrona)
        await callback({"status": "processing", "progress": 80, "message": "Analisando cenas..."})
        ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        video_duration = float(result.stdout.strip())

        # ... (Resto da lógica síncrona) ...
        trocas_de_cena, frames_ordenados = detectar_trocas_de_cena(dados_tags, fps, limiar_similaridade)
        cenas_agrupadas = agrupar_cenas_com_tags(trocas_de_cena, frames_ordenados, dados_tags, fps, video_duration)

        await callback({"status": "processing", "progress": 95, "message": "Salvando resultados..."})
        json_output_path = os.path.join(output_folder, f"{base_name}_cenas.json")
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(cenas_agrupadas, f, indent=4, ensure_ascii=False)

        await callback({"status": "completed", "progress": 100, "message": "Processamento concluído!"})

    except Exception as e:
        await callback({"status": "error", "message": str(e)})
        raise e
    finally:
        if os.path.exists(temp_frames_path):
            shutil.rmtree(temp_frames_path)