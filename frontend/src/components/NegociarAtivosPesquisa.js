import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/NegociarAtivosPesquisa.css';
import config from '../config';


const NegociarAtivosPesquisa = () => {
  const location = useLocation();
  const { simulacaoId } = location.state || {}; // Pega o simulacaoId do estado de navegação
  const [ticker, setTicker] = useState('');
  const [error, setError] = useState('');
  const [showError, setShowError] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!simulacaoId) {
      setError('ID da simulação não encontrado.');
      setShowError(true);
      return;
    }

    try {
      const response = await fetch(`${config}/api/negociar_ativos_pesquisa/${simulacaoId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker })
      });

      const data = await response.json();

      if (response.ok && data.exists) {
        // Passa simulacaoId e ticker no estado de navegação
        navigate(`/negociarativos`, { state: { simulacaoId, ticker } });
      } else {
        setError(`Ativo não encontrado: ${ticker}`);
        setShowError(true);
      }
    } catch (error) {
      console.error('Failed to fetch:', error);
      setError('Falha ao buscar o ativo. Tente novamente mais tarde.');
      setShowError(true);
    }
  };

  return (
    <div className="pesquisar-ativo-container">
      <h2>Pesquisar Ativos</h2>
      <form onSubmit={handleSubmit} className="pesquisar-ativo-form">
        <div className="pesquisar-ativo-input-container">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}  // Converte para maiúsculas
            placeholder="Ticker do ativo de acordo com o Yahoo Finance"
            className="pesquisar-ativo-input"
            required
          />
          <button type="submit" className="pesquisar-ativo-button">
            🔍
          </button>
        </div>
      </form>

      {showError && (
        <div className="error-snackbar" onClick={() => setShowError(false)}>
          <p style={{ color: 'red' }}>{error}</p>
        </div>
      )}
    </div>
  );
};

export default NegociarAtivosPesquisa;
