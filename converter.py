import os
import subprocess
from tqdm import tqdm

# ==============================================================================
# --- CONFIGURAÇÃO ---
# ==============================================================================

# A pasta raiz que contém as subpastas de cada atriz com os vídeos.
VIDEO_ROOT_FOLDER = os.path.join("web", "videos")

# Formatos a serem convertidos. Adicione outros se necessário.
FORMATS_TO_CONVERT = ('.wmv', '.avi', '.mkv', '.mpg', '.mpeg', '.flv', '.mov')

# ==============================================================================
# --- FUNÇÃO PRINCIPAL DE CONVERSÃO ---
# ==============================================================================

def convert_videos_to_mp4():
    """
    Varre as pastas de vídeo, converte formatos antigos para MP4 usando a GPU,
    e deleta os arquivos originais.
    """
    print(f"--- Iniciando a conversão de vídeos em '{VIDEO_ROOT_FOLDER}' para MP4 ---")

    videos_to_convert = []
    # Encontra todos os arquivos que precisam de conversão
    for root, _, files in os.walk(VIDEO_ROOT_FOLDER):
        for file in files:
            if file.lower().endswith(FORMATS_TO_CONVERT):
                videos_to_convert.append(os.path.join(root, file))

    if not videos_to_convert:
        print("Nenhum vídeo para converter. Todos já estão em formato moderno ou a pasta está vazia.")
        return

    print(f"Encontrados {len(videos_to_convert)} vídeos para converter.")

    success_count = 0
    fail_count = 0

    for video_path in tqdm(videos_to_convert, desc="Convertendo vídeos"):
        base_path, _ = os.path.splitext(video_path)
        output_path = f"{base_path}.mp4"
        
        # Comando de conversão com aceleração por GPU (NVENC)
        # '-c:v h264_nvenc' -> Encoder de vídeo da Nvidia
        # '-preset fast' -> Bom equilíbrio de velocidade/qualidade
        # '-c:a aac' -> Codec de áudio padrão e compatível
        command = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-i', video_path,
            '-c:v', 'h264_nvenc',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '192k',
            output_path
        ]

        try:
            # Executa a conversão
            subprocess.run(command, check=True)
            
            # Se a conversão foi bem-sucedida, deleta o original
            os.remove(video_path)
            
            # [CRUCIAL] Renomeia o arquivo JSON correspondente, se existir
            original_json_path = f"{base_path}_cenas.json"
            new_json_path = f"{base_path}.mp4_cenas.json" # Temporário
            final_json_path = f"{base_path}_cenas.json" # O nome final correto

            if os.path.exists(original_json_path):
                # Renomeia para um nome temporário para evitar conflitos se o .mp4 já existia
                os.rename(original_json_path, new_json_path)
                # Renomeia de volta para o nome final, agora que o original se foi
                os.rename(new_json_path, final_json_path)

            success_count += 1
        except subprocess.CalledProcessError:
            tqdm.write(f"  ERRO: Falha ao converter '{os.path.basename(video_path)}'. Pode ser um codec não suportado pela GPU.")
            # Opcional: Adicionar um fallback para CPU aqui se quiser ser exaustivo
            fail_count += 1
        except Exception as e:
            tqdm.write(f"  ERRO inesperado com '{os.path.basename(video_path)}': {e}")
            fail_count += 1
            
    print("\n--- Conversão Concluída ---")
    print(f"✅ Convertidos com sucesso: {success_count}")
    print(f"❌ Falhas: {fail_count}")

if __name__ == "__main__":
    convert_videos_to_mp4()