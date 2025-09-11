import React, { useState } from 'react';
import FolderList from './components/FolderList';
import VideoGrid from './components/VideoGrid';
import PlayerModal from './components/PlayerModal';
import './App.css';

function App() {
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [playingVideo, setPlayingVideo] = useState(null);

  const handleFolderSelect = (folderName) => {
    setSelectedFolder(folderName);
    // Não precisamos mais do reloadKey aqui se o useEffect do VideoGrid for robusto
  };
  
  const handleProcessingComplete = () => {
    setTimeout(() => {
        setReloadKey(prevKey => prevKey + 1);
    }, 1500);
  };

  const handleVideoSelect = (video) => {
    setPlayingVideo(video);
  };

  const handleClosePlayer = () => {
    setPlayingVideo(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Scene Browser</h1>
      </header>
      <div className="main-content">
        <aside className="sidebar">
          <FolderList onFolderSelect={handleFolderSelect} />
        </aside>
        <main className="content">
          <VideoGrid 
            selectedFolder={selectedFolder}
            onProcessingComplete={handleProcessingComplete}
            onVideoSelect={handleVideoSelect}
            keyToReload={reloadKey} // A chave de recarga ainda é útil após o processamento
          />
        </main>
      </div>
      <PlayerModal video={playingVideo} onClose={handleClosePlayer} />
    </div>
  );
}

export default App;