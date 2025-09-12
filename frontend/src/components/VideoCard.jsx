import React from 'react';

const API_URL = 'http://localhost:8000/api';

function VideoCard({ video, onVideoSelect, onProcessingComplete, children }) {
  const thumbnailUrl = `${API_URL}/thumbnail/${encodeURIComponent(video.folder)}/${encodeURIComponent(video.filename)}`;

  return (
    <div className="video-card" onClick={() => onVideoSelect(video)}>
      <div className="video-thumbnail">
        <img src={thumbnailUrl} alt={video.filename} loading="lazy" />
      </div>
      <div className="video-info">
        <p className="video-title" title={video.filename}>{video.filename}</p>
        {/* 'children' nos permite passar conteúdo customizado (como o botão ou o status da busca) */}
        {children}
      </div>
    </div>
  );
}

export default VideoCard;