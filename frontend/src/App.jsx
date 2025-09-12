import React, { useState } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import PlayerModal from './components/PlayerModal';
import BrowserPage from './pages/BrowserPage';
import SearchPage from './pages/SearchPage';
import ManagementPage from './pages/ManagementPage'; // 1. Importe a nova página

import './App.css';

function App() {
  const [reloadKey, setReloadKey] = useState(0);
  const [playingVideo, setPlayingVideo] = useState(null);

  const handleProcessingComplete = () => {
    setTimeout(() => setReloadKey(prev => prev + 1), 1500);
  };
  const handleVideoSelect = (video) => setPlayingVideo(video);
  const handleClosePlayer = () => setPlayingVideo(null);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Scene Browser</h1>
        <nav>
          <Link to="/">Navegador</Link>
          <Link to="/search">Buscar Cenas</Link>
          <Link to="/management">Gerenciar DB</Link> {/* 2. Adicione o novo link */}
        </nav>
      </header>
      
      <Routes>
        <Route
          path="/"
          element={
            <BrowserPage
              onProcessingComplete={handleProcessingComplete}
              onVideoSelect={handleVideoSelect}
              reloadKey={reloadKey}
            />
          }
        />
        <Route 
          path="/search" 
          element={<SearchPage onVideoSelect={handleVideoSelect} />} 
        />
        <Route path="/management" element={<ManagementPage />} /> {/* 3. Adicione a nova rota */}
      </Routes>
      
      <PlayerModal video={playingVideo} onClose={handleClosePlayer} />
    </div>
  );
}

export default App;