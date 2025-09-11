import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// O componente recebe 'props' e desestruturamos para pegar onFolderSelect
function FolderList({ onFolderSelect }) {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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
  }, []);

  if (loading) return <p>Carregando pastas...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div className="folder-list">
      <h2>Estúdios / Atrizes</h2>
      <ul>
        {folders.map(folder => (
          // O onClick chama a função que recebemos via props
          // Adicionamos uma verificação para garantir que é uma função antes de chamar
          <li 
            key={folder} 
            onClick={() => {
              if (typeof onFolderSelect === 'function') {
                onFolderSelect(folder);
              } else {
                console.error("onFolderSelect não é uma função!", onFolderSelect);
              }
            }}
          >
            {folder}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default FolderList;