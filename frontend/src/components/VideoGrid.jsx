import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Este será nosso card individual para cada vídeo
function VideoCard({ video }) {
  const statusIcon = video.has_scenes_json ? '🟢' : '⚪️';
  return (
    <div className="video-card">
      <div className="video-thumbnail">
        {/* Futuramente, aqui virá a imagem de thumbnail */}
        <span>Thumbnail</span>
      </div>
      <div className="video-info">
        <p className="video-title">{video.filename}</p>
        <p className="video-status">Processado: {statusIcon}</p>
      </div>
    </div>
  );
}

function VideoGrid({ selectedFolder }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedFolder) {
      setVideos([]);
      return;
    }

    const fetchVideos = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/videos/${selectedFolder}`);
        setVideos(response.data.videos);
        setError(null);
      } catch (err) {
        setError('Erro ao buscar os vídeos.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [selectedFolder]); // Re-executa sempre que a pasta selecionada mudar

  if (!selectedFolder) {
    return <p className="grid-placeholder">Selecione uma pasta à esquerda para ver os vídeos.</p>;
  }

  if (loading) return <p>Carregando vídeos...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div className="video-grid">
      {videos.length > 0 ? (
        videos.map(video => <VideoCard key={video.filename} video={video} />)
      ) : (
        <p>Nenhum vídeo encontrado nesta pasta.</p>
      )}
    </div>
  );
}

export default VideoGrid;