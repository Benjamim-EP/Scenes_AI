import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/api/ws/progress';

function VideoCard({ video, onProcessingComplete }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState("");

  const handleProcessClick = async () => {
    setIsProcessing(true);
    setProgress("Iniciando...");
    try {
      const response = await axios.post(`${API_URL}/process/${video.folder}/${video.filename}`);
      const { job_id } = response.data;
      
      const ws = new WebSocket(`${WS_URL}/${job_id}`);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgress(data.message);
        if (data.status === 'completed' || data.status === 'error') {
          ws.close();
        }
      };

      ws.onclose = () => {
        setIsProcessing(false);
        onProcessingComplete(); 
      };

      ws.onerror = (event) => {
         console.error("WebSocket Error:", event);
         setProgress("Erro de conexão!");
         setIsProcessing(false);
         onProcessingComplete();
      }

    } catch (err) {
      console.error(err);
      setProgress("Falha ao iniciar!");
      setIsProcessing(false);
    }
  };
  
  const statusIcon = video.has_scenes_json ? '🟢' : '⚪️';
  return (
    <div className="video-card">
      <div className="video-thumbnail"><span>Thumbnail</span></div>
      <div className="video-info">
        <p className="video-title" title={video.filename}>{video.filename}</p>
        <p className="video-status">Processado: {statusIcon}</p>
        {isProcessing ? (
          <div className="progress-bar">{progress}</div>
        ) : (
          !video.has_scenes_json && (
            <button onClick={handleProcessClick} disabled={isProcessing}>
              Processar Cenas
            </button>
          )
        )}
      </div>
    </div>
  );
}

function VideoGrid({ selectedFolder, onProcessingComplete, keyToReload }) {
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
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [selectedFolder, keyToReload]);

  if (!selectedFolder) return <p className="grid-placeholder">Selecione uma pasta para ver os vídeos.</p>;
  if (loading) return <p>Carregando vídeos...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div className="video-grid">
      {videos.length > 0 ? (
        videos.map(video => <VideoCard key={video.filename} video={video} onProcessingComplete={onProcessingComplete} />)
      ) : (
        <p>Nenhum vídeo encontrado nesta pasta.</p>
      )}
    </div>
  );
}
export default VideoGrid;