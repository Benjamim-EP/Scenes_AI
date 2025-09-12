import React, { useState } from 'react';
import axios from 'axios';
import VideoCard from '../components/VideoCard'; // Importa nosso componente reutilizável
import './SearchPage.css';

const API_URL = 'http://localhost:8000/api';

function SearchPage({ onVideoSelect }) { // Recebe onVideoSelect do App.jsx
  const [includeTags, setIncludeTags] = useState('');
  const [excludeTags, setExcludeTags] = useState('');
  const [minDuration, setMinDuration] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSearched(true);
    setSearchResults([]);

    const payload = {
      include_tags: includeTags.split(',').map(tag => tag.trim()).filter(Boolean),
      exclude_tags: excludeTags.split(',').map(tag => tag.trim()).filter(Boolean),
      min_duration: minDuration ? parseFloat(minDuration) : null,
    };

    try {
      // O endpoint correto é /search, não /search_videos
      const response = await axios.post(`${API_URL}/search`, payload);
      setSearchResults(response.data.results);
    } catch (err) {
      setError('A busca falhou. Verifique o console para mais detalhes.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="search-page">
      <form className="search-form" onSubmit={handleSearch}>
        <input type="text" placeholder="Incluir tags (ex: 1girl, blue_hair)" value={includeTags} onChange={(e) => setIncludeTags(e.target.value)} />
        <input type="text" placeholder="Excluir tags (ex: nsfw, solo)" value={excludeTags} onChange={(e) => setExcludeTags(e.target.value)} />
        <input type="number" step="0.1" min="0" placeholder="Duração Mínima da Cena (s)" value={minDuration} onChange={(e) => setMinDuration(e.target.value)} />
        <button type="submit" disabled={isLoading}>{isLoading ? 'Buscando...' : 'Buscar'}</button>
      </form>

      {error && <p className="error-message">{error}</p>}
      
      <div className="video-grid">
        {searchResults.map(video => (
          <VideoCard 
            key={video.video_id} 
            video={video}
            // [A CORREÇÃO ESTÁ AQUI] Passamos a função onVideoSelect para o VideoCard
            onVideoSelect={onVideoSelect} 
          >
            {/* O conteúdo que vai dentro do card, específico para a página de busca */}
            <p className="video-status">{video.match_count} cena(s) encontrada(s)</p>
          </VideoCard>
        ))}
      </div>

      {searched && !isLoading && searchResults.length === 0 && (
        <p className="grid-placeholder">Nenhum vídeo encontrado com esses critérios.</p>
      )}
    </div>
  );
}

export default SearchPage;