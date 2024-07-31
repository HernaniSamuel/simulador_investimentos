import React, { useState } from 'react';
import '../styles/PesquisarAtivo.css'; // Importando o CSS

const PesquisarAtivo = () => {
  const [ticker, setTicker] = useState('');
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const csrfToken = getCookie('csrftoken'); // Função para obter o CSRF token

    try {
      const response = await fetch('http://127.0.0.1:8000/api/pesquisar_ativos/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ ticker })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      if (response.ok) {
        setResultado(data);
        setError('');
      } else {
        setResultado(null);
        setError(data.error);
      }
    } catch (error) {
      console.error('Failed to fetch:', error);
      setError('Failed to fetch');
    }
  };

  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  return (
    <div className="pesquisar-ativo-container">
      <form onSubmit={handleSubmit} className="pesquisar-ativo-form">
        <div className="pesquisar-ativo-input-container">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Ticker do ativo de acordo com o Yahoo Finance"
            className="pesquisar-ativo-input"
            required
          />
          <button type="submit" className="pesquisar-ativo-button">
            🔍
          </button>
        </div>
      </form>
      <div className="pesquisar-ativo-result">
        {resultado && (
          resultado.exists ? (
            <p>Ativo encontrado: {resultado.ticker}</p>
          ) : (
            <p>Ativo não encontrado: {resultado.ticker}</p>
          )
        )}
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>
      {!resultado && !error && (
        <p className="pesquisar-ativo-info">
          Se o ativo existir, seu ticker e nome aparecerão juntamente à opção de adicionar o ativo na carteira.
          Se não existir, será dado um aviso de que o ativo não foi encontrado.
        </p>
      )}
    </div>
  );
};

export default PesquisarAtivo;
