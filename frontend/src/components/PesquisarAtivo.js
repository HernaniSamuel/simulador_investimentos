import React, { useState } from 'react';
import '../styles/PesquisarAtivo.css'; // Importando o CSS
import config from '../config';

const PesquisarAtivo = ({ adicionarAtivo }) => {
  const [ticker, setTicker] = useState('');
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    try {
      const response = await fetch(`${config}/api/pesquisar_ativos/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker })
      });

      const data = await response.json();

      if (response.ok) {
        setResultado(data);
        setError('');
      } else if (response.status === 404) {
        // Ativo não encontrado
        setResultado(data);
        setError('');
      } else {
        // Outro tipo de erro
        setResultado(null);
        setError(data.error || 'Unknown error');
      }
    } catch (error) {
      // Erro de rede ou outra exceção
      console.error('Failed to fetch:', error);
      setError('Failed to fetch');
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
      <div className="pesquisar-ativo-result">
        {resultado && (
          resultado.exists ? (
            <div>
              <p>Ativo encontrado: {resultado.ticker} - {resultado.name}</p>
              <button onClick={() => adicionarAtivo(resultado.ticker)}>Adicionar</button>
            </div>
          ) : (
            <p>Ativo não encontrado: {resultado.ticker} - {resultado.name}</p>
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
