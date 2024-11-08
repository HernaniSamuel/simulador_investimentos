import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/NovaSimulacaoAutomatica.css';
import config from '../config';

const NovaSimulacaoAutomatica = () => {
  const [nome, setNome] = useState('');
  const [anoInicial, setAnoInicial] = useState('');
  const [mesInicial, setMesInicial] = useState('');
  const [anoFinal, setAnoFinal] = useState('');
  const [mesFinal, setMesFinal] = useState('');
  const [aplicacaoInicial, setAplicacaoInicial] = useState('');
  const [aplicacaoMensal, setAplicacaoMensal] = useState('');
  const [moedaBase, setMoedaBase] = useState('BRL'); 
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Monta as datas usando o dia 01
    const dataInicial = `${anoInicial}-${mesInicial}-01`;
    const dataFinal = `${anoFinal}-${mesFinal}-01`;

    if (new Date(dataFinal) < new Date(dataInicial)) {
      setError('A data final não pode ser anterior à data inicial.');
      return;
    }

    const csrfToken = getCookie('csrftoken');

    const response = await fetch(`${config}/api/nova_simulacao_automatica/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        nome,
        data_inicial: dataInicial,
        data_final: dataFinal,
        aplicacao_inicial: aplicacaoInicial,
        aplicacao_mensal: aplicacaoMensal,
        moeda_base: moedaBase
      })
    });

    const data = await response.json();

    if (response.ok) {
      setMessage(data.message);
      setError('');
      navigate('/selecionarativosautomatica', { state: { simulacaoId: data.simulacao_id, carteiraId: data.carteira_id } });
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
      <h2>Criar Nova Simulação Automática</h2>
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

        {/* Seleção de Mês e Ano para Data Inicial */}
        <div className="form-group">
          <label>Data Inicial:</label>
          <select value={mesInicial} onChange={(e) => setMesInicial(e.target.value)} required>
            <option value="">Mês</option>
            <option value="01">Janeiro</option>
            <option value="02">Fevereiro</option>
            <option value="03">Março</option>
            <option value="04">Abril</option>
            <option value="05">Maio</option>
            <option value="06">Junho</option>
            <option value="07">Julho</option>
            <option value="08">Agosto</option>
            <option value="09">Setembro</option>
            <option value="10">Outubro</option>
            <option value="11">Novembro</option>
            <option value="12">Dezembro</option>
          </select>
          <input
            type="number"
            value={anoInicial}
            onChange={(e) => setAnoInicial(e.target.value)}
            placeholder="Ano"
            required
          />
        </div>

        {/* Seleção de Mês e Ano para Data Final */}
        <div className="form-group">
          <label>Data Final:</label>
          <select value={mesFinal} onChange={(e) => setMesFinal(e.target.value)} required>
            <option value="">Mês</option>
            <option value="01">Janeiro</option>
            <option value="02">Fevereiro</option>
            <option value="03">Março</option>
            <option value="04">Abril</option>
            <option value="05">Maio</option>
            <option value="06">Junho</option>
            <option value="07">Julho</option>
            <option value="08">Agosto</option>
            <option value="09">Setembro</option>
            <option value="10">Outubro</option>
            <option value="11">Novembro</option>
            <option value="12">Dezembro</option>
          </select>
          <input
            type="number"
            value={anoFinal}
            onChange={(e) => setAnoFinal(e.target.value)}
            placeholder="Ano"
            required
          />
        </div>

        {/* Outros campos continuam iguais */}
        <div className="form-group">
          <label>Aplicação Inicial:</label>
          <input
            type="number"
            value={aplicacaoInicial}
            onChange={(e) => setAplicacaoInicial(e.target.value)}
            required
            step="any"
          />
        </div>

        <div className="form-group">
          <label>Aplicação Mensal:</label>
          <input
            type="number"
            value={aplicacaoMensal}
            onChange={(e) => setAplicacaoMensal(e.target.value)}
            required
            step="any"
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
          </select>
        </div>
        <button type="submit" className="submit-button">Criar Simulação</button>
      </form>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default NovaSimulacaoAutomatica;
