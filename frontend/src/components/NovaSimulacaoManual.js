import React, { useState } from 'react'; 
import { useNavigate } from 'react-router-dom';
import '../styles/NovaSimulacaoManual.css';

const NovaSimulacaoManual = () => {
  const [nome, setNome] = useState('');
  const [dataInicial, setDataInicial] = useState('');
  const [moedaBase, setMoedaBase] = useState('BRL'); // Default to BRL
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const navigate = useNavigate(); // Hook para navegar entre as páginas

  const handleSubmit = async (e) => {
    e.preventDefault();

    const csrfToken = getCookie('csrftoken');

    const response = await fetch('http://127.0.0.1:8000/api/nova_simulacao_manual/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        nome,
        data_inicial: dataInicial,
        moeda_base: moedaBase
      })
    });

    const data = await response.json();

    if (response.ok) {
      setMessage(data.message);
      setError('');
      // Passar os IDs da simulação e carteira como parte do estado de navegação
      navigate('/simulacaomanual', { state: { simulacaoId: data.simulacao_id, carteiraId: data.carteira_id } });
    } else {
      setMessage('');
      setError(data.error);
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
    <div className="form-container">
      <h2>Criar Nova Simulação Manual</h2>
      <form onSubmit={handleSubmit} className="simulacao-form">
        <div className="form-group">
          <label>Nome da Simulação:</label>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Data Inicial:</label>
          <input
            type="date"
            value={dataInicial}
            onChange={(e) => setDataInicial(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Moeda Base:</label>
          <select
            value={moedaBase}
            onChange={(e) => setMoedaBase(e.target.value)}
            required
          >
            <option value="BRL">BRL - Real Brasileiro</option>
            {/* Adicione outras moedas aqui conforme necessário */}
          </select>
        </div>
        <button type="submit" className="submit-button">Criar Simulação</button>
      </form>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default NovaSimulacaoManual;
