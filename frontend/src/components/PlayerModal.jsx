import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SceneProgressBar from './SceneProgressBar'; // A barra de cenas que criamos
import './PlayerModal.css';

const API_URL = 'http://localhost:8000/api';

function PlayerModal({ video, onClose }) {
  const videoRef = useRef(null); // Referência para o elemento <video>
  const [scenes, setScenes] = useState([]);
  const [videoDuration, setVideoDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  const videoUrl = video ? `${API_URL}/stream/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}` : null;

  // Efeito para buscar os dados das cenas quando o vídeo muda
  useEffect(() => {
    if (video && video.has_scenes_json) { // Só busca se o vídeo foi processado
      const fetchSceneData = async () => {
        try {
          const response = await axios.get(`${API_URL}/scenes/${video.folder}/${video.filename}`);
          setScenes(response.data.scenes);
          // Usaremos a duração do vídeo real em vez da do JSON para mais precisão
        } catch (error) {
          console.error("Erro ao buscar dados das cenas:", error);
          setScenes([]);
        }
      };
      fetchSceneData();
    } else {
      // Limpa os dados se não houver vídeo ou JSON
      setScenes([]);
    }
  }, [video]); // Re-executa quando o 'video' prop muda

  // Função para ser chamada pela barra de progresso
  const handleSeek = (percentage) => {
    if (videoRef.current) {
      const seekTime = videoRef.current.duration * percentage;
      videoRef.current.currentTime = seekTime;
    }
  };

  // Callback para quando os metadados do vídeo (incluindo duração) são carregados
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setVideoDuration(videoRef.current.duration);
      videoRef.current.play().catch(error => {
        console.log("Autoplay impedido pelo navegador:", error);
      });
    }
  };

  // Callback para atualizar o tempo atual enquanto o vídeo toca
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };
  
  if (!video) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        <h3>{video.filename}</h3>
        <div className="player-wrapper">
          {videoUrl && (
            <video
              ref={videoRef}
              key={videoUrl}
              controls
              width="100%"
              height="100%"
              preload="auto"
              onLoadedMetadata={handleLoadedMetadata} // Pega a duração quando o vídeo carrega
              onTimeUpdate={handleTimeUpdate}     // Atualiza o tempo enquanto toca
              style={{ position: 'absolute', top: 0, left: 0, backgroundColor: 'black' }}
            >
              <source src={videoUrl} type="video/mp4" />
              Seu navegador não suporta a tag de vídeo.
            </video>
          )}
        </div>
        
        {/* Renderiza a barra de cenas, passando os dados necessários */}
        <SceneProgressBar
          scenes={scenes}
          duration={videoDuration}
          currentTime={currentTime}
          onSeek={handleSeek}
        />
      </div>
    </div>
  );
}

export default PlayerModal;