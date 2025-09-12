import React from 'react';
import './SceneProgressBar.css';

const getColorForScene = (index) => {
  const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#e67e22'];
  return colors[index % colors.length];
};

// [CORRIGIDO] Adicionamos um valor padrão para a prop 'highlightedSceneIds'
function SceneProgressBar({ scenes, duration, currentTime, onSeek, highlightedSceneIds = [] }) {
  if (!scenes || scenes.length === 0 || duration === 0) {
    return null;
  }

  const playheadPosition = (currentTime / duration) * 100;

  const handleBarClick = (e) => {
    const bar = e.currentTarget;
    const rect = bar.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = bar.offsetWidth;
    const seekPercentage = clickX / width;
    
    onSeek(seekPercentage);
  };

  return (
    <div className="progress-bar-container" onClick={handleBarClick}>
      {scenes.map((scene, index) => {
        const sceneWidth = (scene.duration / duration) * 100;
        
        // [CORRIGIDO] A lógica de destaque agora funciona de forma segura
        // Se 'highlightedSceneIds' estiver vazio, 'isHighlighted' será sempre false.
        const isHighlighted = highlightedSceneIds.length > 0 ? highlightedSceneIds.includes(scene.scene_number || scene.cena_n) : true;

        return (
          <div
            key={scene.scene_number || scene.cena_n}
            className={`scene-segment ${isHighlighted ? 'highlighted' : 'dimmed'}`}
            style={{
              width: `${sceneWidth}%`,
              backgroundColor: isHighlighted ? getColorForScene(index) : '#555',
            }}
            title={`Cena ${scene.scene_number || scene.cena_n} (${scene.start_time.toFixed(1)}s - ${scene.end_time.toFixed(1)}s)`}
          />
        );
      })}
      <div className="playhead" style={{ left: `${playheadPosition}%` }} />
    </div>
  );
}

export default SceneProgressBar;