// frontend/src/components/ProcessModal.jsx
import React, { useState } from 'react';
import './ProcessModal.css';

function ProcessModal({ video, onClose, onStartProcessing }) {
  // Estados para cada parâmetro, com valores padrão
  const [fps, setFps] = useState(1);
  const [threshold, setThreshold] = useState(0.4);
  const [batchSize, setBatchSize] = useState(32);

  if (!video) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const params = {
      fps: parseFloat(fps),
      similarity_threshold: parseFloat(threshold),
      batch_size: parseInt(batchSize, 10),
    };
    onStartProcessing(params); // Envia os parâmetros para o componente pai
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content process-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        <h3>Configurar Análise</h3>
        <p className="modal-video-title">{video.filename}</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="fps">Frames por Segundo (FPS): {fps}</label>
            <input
              type="range" id="fps" min="0.5" max="15" step="0.5"
              value={fps} onChange={(e) => setFps(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="threshold">Limiar de Similaridade: {threshold}</label>
            <input
              type="range" id="threshold" min="0.1" max="0.9" step="0.05"
              value={threshold} onChange={(e) => setThreshold(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="batchSize">Batch Size (GPU): {batchSize}</label>
            <input
              type="range" id="batchSize" min="4" max="128" step="4"
              value={batchSize} onChange={(e) => setBatchSize(e.target.value)}
            />
          </div>
          <button type="submit" className="start-process-btn">
            Iniciar Processamento
          </button>
        </form>
      </div>
    </div>
  );
}

export default ProcessModal;