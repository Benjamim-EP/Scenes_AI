import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SceneProgressBar from './SceneProgressBar';
import './PlayerModal.css';

const API_URL = 'http://localhost:8000/api';

function PlayerModal({ video, onClose }) {
  const videoRef = useRef(null);
  const [sceneData, setSceneData] = useState({ scenes: [], duration: 0 });
  const [currentTime, setCurrentTime] = useState(0);
  
  // --- [NOVA LÓGICA DE NAVEGAÇÃO] ---
  const [currentMatchIndex, setCurrentMatchIndex] = useState(-1);
  const matchingScenes = video?.matching_scenes || []; // Lista de cenas da busca
  const matchingSceneIds = matchingScenes.map(s => s.scene_id); // IDs para o destaque

  const videoUrl = video ? `${API_URL}/stream/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}` : null;

  useEffect(() => {
    setSceneData({ scenes: [], duration: 0 });
    setCurrentTime(0);
    setCurrentMatchIndex(-1); // Reseta o índice da cena

    if (video) {
      const fetchSceneData = async () => {
        try {
          const response = await axios.get(`${API_URL}/scenes/${video.folder}/${video.filename}`);
          setSceneData({
            scenes: response.data.scenes || [],
            duration: response.data.duration || 0
          });
        } catch (error) { console.error("Erro ao buscar dados das cenas:", error); }
      };
      fetchSceneData();
    }
  }, [video]);

  const handleSeek = (percentage) => {
    if (videoRef.current) {
      videoRef.current.currentTime = sceneData.duration * percentage;
    }
  };

  // Função para pular para o início de uma cena específica
  const jumpToScene = (scene) => {
    if (videoRef.current && scene) {
      videoRef.current.currentTime = scene.start_time;
      videoRef.current.play();
    }
  };

  // --- [NOVAS FUNÇÕES] para os botões de navegação ---
  const handleNextScene = () => {
    const nextIndex = currentMatchIndex + 1;
    if (nextIndex < matchingScenes.length) {
      setCurrentMatchIndex(nextIndex);
      jumpToScene(matchingScenes[nextIndex]);
    }
  };

  const handlePrevScene = () => {
    const prevIndex = currentMatchIndex - 1;
    if (prevIndex >= 0) {
      setCurrentMatchIndex(prevIndex);
      jumpToScene(matchingScenes[prevIndex]);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      // Se viemos de uma busca, pula para a primeira cena encontrada
      if (matchingScenes.length > 0) {
        setCurrentMatchIndex(0);
        jumpToScene(matchingScenes[0]);
      } else {
        videoRef.current.play().catch(error => console.log("Autoplay impedido:", error));
      }
    }
  };

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
              onLoadedMetadata={handleLoadedMetadata}
              onTimeUpdate={handleTimeUpdate}
              style={{ position: 'absolute', top: 0, left: 0, backgroundColor: 'black' }}
            >
              <source src={videoUrl} type="video/mp4" />
              Seu navegador não suporta a tag de vídeo.
            </video>
          )}
        </div>
        
        <SceneProgressBar
          scenes={sceneData.scenes}
          duration={sceneData.duration}
          currentTime={currentTime}
          onSeek={handleSeek}
          highlightedSceneIds={matchingSceneIds}
        />

        {/* --- [NOVO] Controles de Navegação de Cena --- */}
        {matchingScenes.length > 0 && (
          <div className="scene-nav-controls">
            <button onClick={handlePrevScene} disabled={currentMatchIndex <= 0}>
              &lt; Cena Anterior
            </button>
            <span>
              Cena Encontrada: {currentMatchIndex + 1} / {matchingScenes.length}
            </span>
            <button onClick={handleNextScene} disabled={currentMatchIndex >= matchingScenes.length - 1}>
              Próxima Cena &gt;
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default PlayerModal;