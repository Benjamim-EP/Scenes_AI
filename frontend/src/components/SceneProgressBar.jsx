import React from 'react';
import './SceneProgressBar.css'; // Vamos criar este arquivo de estilo

// Função para gerar uma cor com base no número da cena para variedade visual
const getColorForScene = (index) => {
  const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#e67e22'];
  return colors[index % colors.length];
};

function SceneProgressBar({ scenes, duration, currentTime, onSeek }) {
  if (!scenes || scenes.length === 0 || duration === 0) {
    return null; // Não renderiza nada se não houver dados
  }

  // Calcula a posição do playhead em porcentagem
  const playheadPosition = (currentTime / duration) * 100;

  const handleBarClick = (e) => {
    // Pega a referência do elemento da barra para calcular a posição do clique
    const bar = e.currentTarget;
    const rect = bar.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = bar.offsetWidth;
    const seekPercentage = clickX / width;
    
    // Chama a função onSeek passada pelo pai (PlayerModal)
    onSeek(seekPercentage);
  };

  return (
    <div className="progress-bar-container" onClick={handleBarClick}>
      {scenes.map((scene, index) => {
        const sceneWidth = (scene.duration / duration) * 100;
        return (
          <div
            key={scene.cena_n}
            className="scene-segment"
            style={{
              width: `${sceneWidth}%`,
              backgroundColor: getColorForScene(index),
            }}
            title={`Cena ${scene.cena_n} (${scene.start_time.toFixed(1)}s - ${scene.end_time.toFixed(1)}s)`}
          />
        );
      })}
      <div className="playhead" style={{ left: `${playheadPosition}%` }} />
    </div>
  );
}

export default SceneProgressBar;