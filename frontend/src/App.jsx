import React, { useState } from 'react';
import FolderList from './components/FolderList';
import VideoGrid from './components/VideoGrid';
import './App.css';

function App() {
  const [selectedFolder, setSelectedFolder] = useState(null);

  // A função que será passada para o FolderList
  const handleFolderSelect = (folderName) => {
    console.log("Pasta selecionada em App.jsx:", folderName); // Adicionado para debug
    setSelectedFolder(folderName);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Scene Browser</h1>
      </header>
      <div className="main-content">
        <aside className="sidebar">
          {/* Aqui, estamos passando a função handleFolderSelect como a prop onFolderSelect */}
          <FolderList onFolderSelect={handleFolderSelect} />
        </aside>
        <main className="content">
          <VideoGrid selectedFolder={selectedFolder} />
        </main>
      </div>
    </div>
  );
}

export default App;