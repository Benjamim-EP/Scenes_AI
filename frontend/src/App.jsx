import React, { useState } from 'react';
import FolderList from './components/FolderList';
import VideoGrid from './components/VideoGrid';
import './App.css';

function App() {
  // Estado para guardar o nome da pasta que o usuário selecionou
  // Inicia como null para sabermos que nenhuma pasta foi escolhida ainda
  const [selectedFolder, setSelectedFolder] = useState(null);

  // Estado para forçar a recarga do VideoGrid
  // Toda vez que este número mudar, o useEffect no VideoGrid será re-executado
  const [reloadKey, setReloadKey] = useState(0);

  // Esta função é passada como uma propriedade para o FolderList
  // e será chamada quando o usuário clicar em uma pasta
  const handleFolderSelect = (folderName) => {
    // Atualiza o estado com o nome da nova pasta selecionada
    setSelectedFolder(folderName);
    // Reinicia a chave de recarga para garantir que os dados sejam buscados novamente
    setReloadKey(prevKey => prevKey + 1);
  };
  
  // Esta função é passada até o VideoCard
  // e será chamada quando um processo de vídeo terminar (com sucesso ou falha)
  const handleProcessingComplete = () => {
    // Adiciona um pequeno atraso para dar tempo ao sistema de arquivos do servidor
    // de registrar o novo arquivo .json antes de recarregar a lista.
    setTimeout(() => {
        // Incrementa a chave, o que forçará o VideoGrid a buscar os dados novamente
        setReloadKey(prevKey => prevKey + 1);
    }, 1500); // 1.5 segundos de atraso
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Scene Browser</h1>
      </header>
      <div className="main-content">
        <aside className="sidebar">
          {/* O FolderList recebe a função para notificar o App sobre a seleção */}
          <FolderList onFolderSelect={handleFolderSelect} />
        </aside>
        <main className="content">
          {/* O VideoGrid recebe a pasta selecionada para buscar os vídeos */}
          {/* e a função para notificar o App quando um processamento termina */}
          {/* A `key` especial e `reloadKey` garantem a remontagem e recarga */}
          <VideoGrid 
            key={selectedFolder + reloadKey} // Força a remontagem do componente
            selectedFolder={selectedFolder}
            onProcessingComplete={handleProcessingComplete}
          />
        </main>
      </div>
    </div>
  );
}

export default App;