// frontend/src/pages/BrowserPage.jsx
import React, { useState } from 'react';
import FolderList from '../components/FolderList';
import VideoGrid from '../components/VideoGrid';

function BrowserPage({ onVideoSelect, onProcessingComplete, reloadKey }) {
  const [selectedFolder, setSelectedFolder] = useState(null);

  const handleFolderSelect = (folderName) => {
    setSelectedFolder(folderName);
  };

  return (
    <div className="main-content">
      <aside className="sidebar">
        <FolderList onFolderSelect={handleFolderSelect} />
      </aside>
      <main className="content">
        <VideoGrid
          key={selectedFolder + reloadKey}
          selectedFolder={selectedFolder}
          onProcessingComplete={onProcessingComplete}
          onVideoSelect={onVideoSelect}
        />
      </main>
    </div>
  );
}

export default BrowserPage;