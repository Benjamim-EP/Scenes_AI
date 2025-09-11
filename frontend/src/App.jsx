import React from 'react';
import FolderList from './components/FolderList';
import './App.css'; // Vamos usar este arquivo para um pouco de estilo

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Scene Browser</h1>
      </header>
      <main>
        <FolderList />
      </main>
    </div>
  );
}

export default App;