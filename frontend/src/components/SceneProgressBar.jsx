import React from 'react';
import './SceneProgressBar.css';

const getColorForScene = (index) => {
  const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#e67e22'];
  return colors[index % colors.length];
};

function SceneProgressBar({ scenes, duration, currentTime, onSeek, highlightedSceneIds = [] }) {
  if (!scenes || scenes.length === 0 || duration <= 0) {
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

  const isSearchMode = highlightedSceneIds.length > 0;

  return (
    <div className="progress-bar-container" onClick={handleBarClick}>
      {scenes.map((scene, index) => {
        const sceneWidth = (scene.duration / duration) * 100;
        
        // [A CORREÇÃO] Agora comparamos com 'scene.scene_id'
        const isHighlighted = !isSearchMode || highlightedSceneIds.includes(scene.scene_id);

        return (
          <div
            key={scene.scene_id || scene.cena_n} // Usa scene_id como chave, se disponível
            className="scene-segment"
            style={{
              width: `${sceneWidth}%`,
              backgroundColor: getColorForScene(index),
              opacity: isHighlighted ? 1 : 0.3
            }}
            title={`Cena ${scene.cena_n} (ID: ${scene.scene_id})`}
          />
        );
      })}
      <div className="playhead" style={{ left: `${playheadPosition}%` }} />
    </div>
  );
}

export default SceneProgressBar;