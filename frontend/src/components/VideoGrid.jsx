import React, { useState, useEffect } from 'react';
import axios from 'axios';

// --- Constantes para as URLs da API ---
const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/api/ws/progress';

// ==============================================================================
// --- Componente VideoCard (Card Individual para cada vídeo) ---
// ==============================================================================
function VideoCard({ video, onProcessingComplete, onVideoSelect }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");

  const thumbnailUrl = `${API_URL}/thumbnail/${video.folder}/${video.filename}`;

  // Função para iniciar o processo de análise de cenas
  const handleProcessClick = async (e) => {
    e.stopPropagation(); // Impede que o clique no botão também abra o player
    setIsProcessing(true);
    setProgressMessage("Iniciando...");

    try {
      // 1. Inicia o processo no backend
      const response = await axios.post(`${API_URL}/process/${video.folder}/${video.filename}`);
      const { job_id } = response.data;
      
      // 2. Conecta ao WebSocket para receber atualizações
      const ws = new WebSocket(`${WS_URL}/${job_id}`);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgressMessage(`${data.message} (${data.progress || 0}%)`);
        if (data.status === 'completed' || data.status === 'error') {
          ws.close();
        }
      };

      ws.onclose = () => {
        setIsProcessing(false);
        // Chama a função do componente pai para recarregar a lista de vídeos
        if (typeof onProcessingComplete === 'function') {
          onProcessingComplete();
        }
      };

      ws.onerror = (event) => {
         console.error("WebSocket Error:", event);
         setProgressMessage("Erro de conexão!");
         setIsProcessing(false);
         if (typeof onProcessingComplete === 'function') {
            onProcessingComplete();
         }
      }

    } catch (err) {
      console.error("Falha ao iniciar o processo:", err);
      setProgressMessage("Falha ao iniciar!");
      setIsProcessing(false);
    }
  };
  
  const statusIcon = video.has_scenes_json ? '🟢' : '⚪️';
  
  return (
    // O onClick no card principal abre o player de vídeo
    <div className="video-card" onClick={() => onVideoSelect(video)}>
      <div className="video-thumbnail">
        <img src={thumbnailUrl} alt={video.filename} loading="lazy" />
      </div>
      <div className="video-info">
        <p className="video-title" title={video.filename}>{video.filename}</p>
        <p className="video-status">Processado: {statusIcon}</p>
        
        {/* Lógica condicional para o botão ou a barra de progresso */}
        {isProcessing ? (
          <div className="progress-bar">{progressMessage}</div>
        ) : (
          // Mostra o botão "Reprocessar" se já tiver JSON, ou "Processar" se não tiver
          <button onClick={handleProcessClick} disabled={isProcessing}>
            {video.has_scenes_json ? 'Reprocessar Cenas' : 'Processar Cenas'}
          </button>
        )}
      </div>
    </div>
  );
}

// ==============================================================================
// --- Componente VideoGrid (O container para todos os cards) ---
// ==============================================================================
function VideoGrid({ selectedFolder, onProcessingComplete, onVideoSelect, keyToReload }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Não faz nada se nenhuma pasta estiver selecionada
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
        setError('Erro ao buscar os vídeos. Verifique se o backend está rodando.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [selectedFolder, keyToReload]); // Re-executa quando a pasta selecionada ou a chave de recarga mudam

  // --- Renderização condicional baseada no estado ---
  if (!selectedFolder) {
    return <p className="grid-placeholder">Selecione uma pasta à esquerda para ver os vídeos.</p>;
  }

  if (loading) {
    return <p className="grid-placeholder">Carregando vídeos...</p>;
  }

  if (error) {
    return <p style={{ color: '#ff6b6b' }}>{error}</p>;
  }

  return (
    <div className="video-grid">
      {videos.length > 0 ? (
        videos.map(video => (
          <VideoCard 
            key={video.filename} 
            video={video} 
            onProcessingComplete={onProcessingComplete}
            onVideoSelect={onVideoSelect}
          />
        ))
      ) : (
        <p className="grid-placeholder">Nenhum arquivo de vídeo encontrado nesta pasta.</p>
      )}
    </div>
  );
}

export default VideoGrid;