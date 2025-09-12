import React, { useState, useEffect } from 'react';
import axios from 'axios';
import VideoCard from './VideoCard';
import ProcessModal from './ProcessModal'; // Importa o novo modal de configuração

const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/api/ws/progress';

// ==============================================================================
// --- Conteúdo Específico do Card para o Modo Navegador ---
// ==============================================================================
function BrowserCardContent({ video, onProcessingComplete }) {
  const [isProcessing, setIsProcessing] = useState(false);
  // [MODIFICADO] Estado para guardar o objeto de progresso completo
  const [progress, setProgress] = useState({ message: "", progress: 0 });
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  const handleProcessClick = (e) => {
    e.stopPropagation();
    setIsConfigModalOpen(true);
  };

  const handleStartProcessing = async (params) => {
    setIsConfigModalOpen(false);
    setIsProcessing(true);
    setProgress({ message: "Iniciando...", progress: 0 });

    try {
      const response = await axios.post(`${API_URL}/process/${video.folder}/${video.filename}`, params);
      const { job_id } = response.data;
      
      const ws = new WebSocket(`${WS_URL}/${job_id}`);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // [MODIFICADO] Atualiza o estado com o objeto de progresso completo
        setProgress(data); 
        if (data.status === 'completed' || data.status === 'error') {
          ws.close();
        }
      };

      ws.onclose = () => {
        setIsProcessing(false);
        // Mantém a última mensagem (Concluído! ou Erro) por um tempo antes de recarregar
        setTimeout(() => {
          if (typeof onProcessingComplete === 'function') {
            onProcessingComplete();
          }
        }, 2000); // Atraso de 2 segundos
      };

      ws.onerror = (event) => {
         console.error("WebSocket Error:", event);
         setProgress({ message: "Erro de conexão!", progress: 0 });
         setIsProcessing(false);
         if (typeof onProcessingComplete === 'function') {
            onProcessingComplete();
         }
      };

    } catch (err) {
      console.error("Falha ao iniciar o processo:", err);
      setProgress({ message: "Falha ao iniciar!", progress: 0 });
      setIsProcessing(false);
    }
  };
  
  const statusIcon = video.has_scenes_json ? '🟢' : '⚪️';
  
  return (
    <>
      <p className="video-status">Processado: {statusIcon}</p>
      
      {isProcessing ? (
        // [MODIFICADO] Renderiza a nova estrutura de progresso
        <div className="progress-container">
          <span className="progress-message">{progress.message}</span>
          <progress className="progress-bar-element" value={progress.progress} max="100" />
        </div>
      ) : (
        <button onClick={handleProcessClick}>
          {video.has_scenes_json ? 'Reprocessar Cenas' : 'Processar Cenas'}
        </button>
      )}

      {isConfigModalOpen && (
        <ProcessModal 
          video={video} 
          onClose={() => setIsConfigModalOpen(false)}
          onStartProcessing={handleStartProcessing}
        />
      )}
    </>
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
  }, [selectedFolder, keyToReload]);

  if (!selectedFolder) {
    return <p className="grid-placeholder">Selecione uma pasta para ver os vídeos.</p>;
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
            onVideoSelect={onVideoSelect}
          >
            {/* O conteúdo dinâmico do card é passado como 'children' */}
            <BrowserCardContent 
              video={video} 
              onProcessingComplete={onProcessingComplete} 
            />
          </VideoCard>
        ))
      ) : (
        <p className="grid-placeholder">Nenhum vídeo encontrado nesta pasta.</p>
      )}
    </div>
  );
}

export default VideoGrid;