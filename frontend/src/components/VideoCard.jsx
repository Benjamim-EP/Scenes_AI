import React from 'react';

const API_URL = 'http://localhost:8000/api';

function VideoCard({ video, onVideoSelect, children }) {
  // A URL da thumbnail é construída a partir dos dados do vídeo
  const thumbnailUrl = `${API_URL}/thumbnail/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}`;

  return (
    // O onClick agora chama a função recebida via props
    <div className="video-card" onClick={() => onVideoSelect(video)}>
      <div className="video-thumbnail">
        <img src={thumbnailUrl} alt={video.filename} loading="lazy" />
      </div>
      <div className="video-info">
        <p className="video-title" title={video.filename}>{video.filename}</p>
        {/* 'children' permite que cada página insira seu próprio conteúdo de status */}
        {children}
      </div>
    </div>
  );
}

export default VideoCard;