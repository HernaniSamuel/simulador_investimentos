import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/Historico.css';

const Historico = () => {
  const [historico, setHistorico] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistorico = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/historico/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setHistorico(data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistorico();
  }, []);

  const handleDelete = async (simulacaoId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/excluir_simulacao/${simulacaoId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      setHistorico(historico.map(h => ({
        ...h,
        simulacoes: h.simulacoes.filter(simulacao => simulacao.simulacao_id !== simulacaoId)
      })));
    } catch (error) {
      setError(error.message);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="historico-container">
      <h1>Histórico de Simulações</h1>
      <div className="historico-list">
        {historico.map(item => (
          item.simulacoes.map(simulacao => (
            <div key={simulacao.simulacao_id} className="simulacao-card">
              <h2>{simulacao.nome}</h2>
              <p>Data Inicial: {simulacao.data_inicial}</p>
              <p>Data Final: {simulacao.data_final}</p>
              <p>Aplicação Inicial: {simulacao.aplicacao_inicial}</p>
              <p>Aplicação Mensal: {simulacao.aplicacao_mensal}</p>

              <Link to={`/abrirsimulacaoautomatica/${simulacao.simulacao_id}`} className="open-simulacao-link">
                Abrir Simulação
              </Link>
              <button onClick={() => handleDelete(simulacao.simulacao_id)}>Excluir</button>
            </div>
          ))
        ))}
      </div>
    </div>
  );
};

export default Historico;
