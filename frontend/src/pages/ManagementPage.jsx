import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ManagementPage.css';

const API_URL = 'http://localhost:8000/api';

function ManagementPage() {
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false); // Novo estado para o botão de limpeza
  const [isScanning, setIsScanning] = useState(false); // Novo estado para o botão de scan
  const [error, setError] = useState('');
  const [actionMessage, setActionMessage] = useState(''); // Mensagem de feedback das ações

  const fetchStatus = async () => {
    setIsLoading(true);
    setError('');
    setActionMessage(''); // Limpa a mensagem de ação anterior
    try {
      const response = await axios.get(`${API_URL}/management/status`);
      setStatus(response.data);
    } catch (err) {
      setError('Falha ao buscar o status do banco de dados.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  // --- NOVAS FUNÇÕES DE AÇÃO ---
  const handleCleanup = async () => {
    if (!status || status.orphan_records.length === 0) return;
    
    setIsCleaning(true);
    setActionMessage('');
    try {
      const response = await axios.post(`${API_URL}/management/cleanup`, {
        paths: status.orphan_records
      });
      setActionMessage(`Sucesso! ${response.data.deleted_count} registro(s) removido(s).`);
      // Atualiza o status para refletir as mudanças
      fetchStatus();
    } catch (err) {
      setActionMessage('Erro durante a limpeza. Verifique o console.');
      console.error(err);
    } finally {
      setIsCleaning(false);
    }
  };

  const handleScanNew = async () => {
    if (!status || status.untracked_files.length === 0) return;

    setIsScanning(true);
    setActionMessage('');
    try {
      const response = await axios.post(`${API_URL}/management/scan_new`, {
        paths: status.untracked_files
      });
      setActionMessage(response.data.message);
      // Atualiza o status
      fetchStatus();
    } catch (err) {
      setActionMessage('Erro ao adicionar novos vídeos. Verifique o console.');
      console.error(err);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="management-page">
      <h2>Gerenciamento do Banco de Dados</h2>
      <button onClick={fetchStatus} disabled={isLoading || isCleaning || isScanning} className="refresh-btn">
        {isLoading ? 'Verificando...' : 'Verificar Status Novamente'}
      </button>

      {actionMessage && <p className="action-message">{actionMessage}</p>}
      {error && <p className="error-message">{error}</p>}

      {status && !isLoading && (
        <div className="status-container">
          {/* ... (Seção de Resumo - sem alteração) ... */}
          <div className="summary-grid"> ... </div>

          {/* Seção de Registros Órfãos (com botão funcional) */}
          <div className="section-card">
            <h3>Registros Órfãos ({status.orphan_records.length})</h3>
            <p>Estes vídeos estão no banco de dados, mas os arquivos não foram encontrados.</p>
            {status.orphan_records.length > 0 ? (
              <>
                <ul className="file-list">
                  {status.orphan_records.map(path => <li key={path}>{path}</li>)}
                </ul>
                <button onClick={handleCleanup} disabled={isCleaning} className="action-btn danger">
                  {isCleaning ? 'Limpando...' : `Limpar ${status.orphan_records.length} Registro(s) Órfão(s)`}
                </button>
              </>
            ) : (
              <p className="no-issues">Nenhum registro órfão encontrado. ✅</p>
            )}
          </div>

          {/* Seção de Arquivos Não Catalogados (com botão funcional) */}
          <div className="section-card">
            <h3>Arquivos Não Catalogados ({status.untracked_files.length})</h3>
            <p>Estes vídeos estão nas pastas, mas ainda não foram adicionados ao banco de dados.</p>
            {status.untracked_files.length > 0 ? (
              <>
                <ul className="file-list">
                  {status.untracked_files.map(path => <li key={path}>{path}</li>)}
                </ul>
                <button onClick={handleScanNew} disabled={isScanning} className="action-btn">
                  {isScanning ? 'Adicionando...' : `Adicionar ${status.untracked_files.length} Novo(s) Vídeo(s)`}
                </button>
              </>
            ) : (
              <p className="no-issues">Todos os vídeos estão catalogados. ✅</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ManagementPage;