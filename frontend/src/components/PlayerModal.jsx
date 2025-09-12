import React, { useState, useEffect, useRef } from 'react'; // [CORRIGIDO] Adicionado useState, useEffect, useRef
import axios from 'axios';
import SceneProgressBar from './SceneProgressBar';
import './PlayerModal.css';

const API_URL = 'http://localhost:8000/api';

function PlayerModal({ video, onClose }) {
  const videoRef = useRef(null);
  const [scenes, setScenes] = useState([]);
  const [videoDuration, setVideoDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  // Pega a lista de IDs de cenas correspondentes, se a prop 'video' as tiver
  const matchingSceneIds = video?.matching_scene_ids || [];

  const videoUrl = video ? `${API_URL}/stream/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}` : null;

  useEffect(() => {
    // Limpa os dados antigos sempre que um novo vídeo é selecionado
    setScenes([]);
    setVideoDuration(0);
    setCurrentTime(0);

    if (video && video.has_scenes_json) {
      const fetchSceneData = async () => {
        try {
          const response = await axios.get(`${API_URL}/scenes/${video.folder}/${video.filename}`);
          setScenes(response.data.scenes);
        } catch (error) {
          console.error("Erro ao buscar dados das cenas:", error);
          setScenes([]);
        }
      };
      fetchSceneData();
    }
  }, [video]); // Re-executa quando o 'video' prop muda

  const handleSeek = (percentage) => {
    if (videoRef.current) {
      videoRef.current.currentTime = videoRef.current.duration * percentage;
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setVideoDuration(videoRef.current.duration);
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
          scenes={scenes}
          duration={videoDuration}
          currentTime={currentTime}
          onSeek={handleSeek}
          highlightedSceneIds={matchingSceneIds}
        />
      </div>
    </div>
  );
}

export default PlayerModal;