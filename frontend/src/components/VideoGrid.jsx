import React, { useState, useEffect } from 'react';
import axios from 'axios';
import VideoCard from './VideoCard'; // Importa o componente reutilizável

const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/api/ws/progress';

// Componente para o conteúdo específico do card no modo Browser
function BrowserCardContent({ video, onProcessingComplete }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");

  const handleProcessClick = async (e) => {
    e.stopPropagation();
    setIsProcessing(true);
    setProgressMessage("Iniciando...");
    try {
      const response = await axios.post(`${API_URL}/process/${video.folder}/${video.filename}`);
      const { job_id } = response.data;
      const ws = new WebSocket(`${WS_URL}/${job_id}`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgressMessage(`${data.message} (${data.progress || 0}%)`);
        if (data.status === 'completed' || data.status === 'error') ws.close();
      };
      ws.onclose = () => {
        setIsProcessing(false);
        if (typeof onProcessingComplete === 'function') onProcessingComplete();
      };
      ws.onerror = () => {
         setProgressMessage("Erro de conexão!");
         setIsProcessing(false);
         if (typeof onProcessingComplete === 'function') onProcessingComplete();
      }
    } catch (err) {
      setProgressMessage("Falha ao iniciar!");
      setIsProcessing(false);
    }
  };
  
  const statusIcon = video.has_scenes_json ? '🟢' : '⚪️';
  
  return (
    <>
      <p className="video-status">Processado: {statusIcon}</p>
      {isProcessing ? (
        <div className="progress-bar">{progressMessage}</div>
      ) : (
        <button onClick={handleProcessClick} disabled={isProcessing}>
          {video.has_scenes_json ? 'Reprocessar' : 'Processar Cenas'}
        </button>
      )}
    </>
  );
}

function VideoGrid({ selectedFolder, onProcessingComplete, onVideoSelect, keyToReload }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedFolder) { setVideos([]); return; }
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
  if (loading) return <p className="grid-placeholder">Carregando vídeos...</p>;
  if (error) return <p style={{ color: '#ff6b6b' }}>{error}</p>;

  return (
    <div className="video-grid">
      {videos.length > 0 ? (
        videos.map(video => (
          <VideoCard 
            key={video.filename} 
            video={video} 
            onVideoSelect={onVideoSelect}
          >
            <BrowserCardContent video={video} onProcessingComplete={onProcessingComplete} />
          </VideoCard>
        ))
      ) : (
        <p className="grid-placeholder">Nenhum vídeo encontrado nesta pasta.</p>
      )}
    </div>
  );
}
export default VideoGrid;