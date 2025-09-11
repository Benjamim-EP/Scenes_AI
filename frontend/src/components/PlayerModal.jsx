import React, { useEffect, useRef } from 'react';
import './PlayerModal.css';

const API_URL = 'http://localhost:8000/api';

function PlayerModal({ video, onClose }) {
  // useRef é usado para obter uma referência direta ao elemento <video> no DOM
  const videoRef = useRef(null);

  useEffect(() => {
    // Este efeito é executado quando o modal é aberto ou o vídeo muda
    // Ele garante que o vídeo comece a tocar (se o navegador permitir)
    if (videoRef.current) {
      videoRef.current.play().catch(error => {
        // O autoplay pode ser bloqueado pelo navegador, isso é normal.
        // O usuário pode simplesmente clicar no play.
        console.log("Autoplay foi impedido pelo navegador:", error);
      });
    }
  }, [video]); // Depende do objeto 'video'

  if (!video) return null;

  const videoUrl = video && video.folder && video.filename 
    ? `${API_URL}/stream/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}`
    : null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        <h3>{video.filename}</h3>
        <div className="player-wrapper">
          {videoUrl ? (
            // [MODIFICADO] Substituímos o ReactPlayer pela tag <video> nativa
            <video
              ref={videoRef}
              key={videoUrl} // A key ainda é importante para recriar o elemento
              controls
              width="100%"
              height="100%"
              preload="auto"
              style={{ position: 'absolute', top: 0, left: 0, backgroundColor: 'black' }}
            >
              <source src={videoUrl} type="video/mp4" />
              Seu navegador não suporta a tag de vídeo.
            </video>
          ) : (
            <p>Construindo URL do vídeo...</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default PlayerModal;