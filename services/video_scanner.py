# services/video_scanner.py

import os
from typing import Dict, List, Any

class VideoScanner:
    """
    Responsável por escanear um diretório em busca de arquivos de vídeo
    organizados em subpastas.
    """
    VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']

    def __init__(self, root_path: str):
        if not os.path.isdir(root_path):
            raise FileNotFoundError(f"O diretório raiz especificado não existe: {root_path}")
        self.root_path = root_path

    def scan(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Executa o escaneamento e retorna um dicionário com os dados dos vídeos.
        Formato: {'Nome da Atriz': [{'name': 'Nome do Video', 'path': 'caminho/completo'}]}
        """
        video_data = {}
        
        try:
            # Lista as pastas (atrizes) dentro do diretório raiz
            actress_folders = [d for d in os.listdir(self.root_path) if os.path.isdir(os.path.join(self.root_path, d))]

            for actress in sorted(actress_folders): # Ordena para consistência
                actress_path = os.path.join(self.root_path, actress)
                videos = []
                
                # Lista os arquivos dentro da pasta da atriz
                for filename in sorted(os.listdir(actress_path)):
                    if any(filename.lower().endswith(ext) for ext in self.VIDEO_EXTENSIONS):
                        video_info = {
                            "name": os.path.splitext(filename)[0],
                            "path": os.path.join(actress_path, filename)
                        }
                        videos.append(video_info)
                
                if videos:
                    video_data[actress] = videos
                    
        except Exception as e:
            print(f"Ocorreu um erro ao escanear a pasta: {e}")
            return {} # Retorna um objeto vazio em caso de erro

        return video_data