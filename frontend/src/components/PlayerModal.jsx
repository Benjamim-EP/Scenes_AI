import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SceneProgressBar from './SceneProgressBar';
import './PlayerModal.css';

const API_URL = 'http://localhost:8000/api';

function PlayerModal({ video, onClose }) {
  const videoRef = useRef(null);
  const [sceneData, setSceneData] = useState({ scenes: [], duration: 0 });
  const [currentTime, setCurrentTime] = useState(0);

  const matchingSceneIds = video?.matching_scene_ids || [];
  const videoUrl = video ? `${API_URL}/stream/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}` : null;

  useEffect(() => {
    setSceneData({ scenes: [], duration: 0 });
    setCurrentTime(0);

    // [A CORREÇÃO] A condição agora é mais simples: se temos um vídeo, tentamos buscar as cenas.
    // A API retornará uma lista vazia se o JSON não existir, o que é um comportamento seguro.
    if (video) { 
      const fetchSceneData = async () => {
        try {
          const response = await axios.get(`${API_URL}/scenes/${video.folder}/${video.filename}`);
          setSceneData({
            scenes: response.data.scenes || [],
            duration: response.data.duration || 0
          });
        } catch (error) {
          console.error("Erro ao buscar dados das cenas:", error);
          setSceneData({ scenes: [], duration: 0 });
        }
      };
      fetchSceneData();
    }
  }, [video]);

  // ... (o resto do código: handleSeek, handleLoadedMetadata, etc. permanece igual)
  const handleSeek = (percentage) => {
    if (videoRef.current) {
      videoRef.current.currentTime = sceneData.duration * percentage;
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      videoRef.current.play().catch(error => {
        console.log("Autoplay impedido pelo navegador:", error);
      });
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
      </div>
    </div>
  );
}

export default PlayerModal;