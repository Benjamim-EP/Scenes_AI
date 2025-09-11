import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api'; // URL do nosso backend

function FolderList() {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Esta função é executada quando o componente é montado
    const fetchFolders = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/folders`);
        setFolders(response.data.folders);
        setError(null);
      } catch (err) {
        setError('Erro ao buscar as pastas. O backend está rodando?');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchFolders();
  }, []); // O array vazio [] garante que isso rode apenas uma vez

  if (loading) return <p>Carregando pastas...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div className="folder-list">
      <h2>Estúdios / Atrizes</h2>
      <ul>
        {folders.map(folder => (
          <li key={folder}>{folder}</li>
        ))}
      </ul>
    </div>
  );
}

export default FolderList;