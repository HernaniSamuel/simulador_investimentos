import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Historico.css';

const Historico = () => {
  const [historico, setHistorico] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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

        if (Array.isArray(data)) {
          setHistorico(data);
        } else {
          throw new Error('Unexpected data format');
        }
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistorico();
  }, []);

  const handleDeleteManual = async (simulacaoId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/excluir_simulacao_manual/${simulacaoId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      // Atualizar o estado após exclusão
      setHistorico(prevHistorico =>
        prevHistorico.map(h => ({
          ...h,
          simulacoes_automaticas: h.simulacoes_automaticas.filter(simulacao => simulacao.simulacao_id !== simulacaoId),
          simulacoes_manuais: h.simulacoes_manuais.filter(simulacao => simulacao.simulacao_id !== simulacaoId),
        }))
      );
    } catch (error) {
      setError(error.message);
    }
  };

  const handleDeleteAutomatica = async (simulacaoId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/excluir_simulacao_automatica/${simulacaoId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      // Atualizar o estado após exclusão
      setHistorico(prevHistorico =>
        prevHistorico.map(h => ({
          ...h,
          simulacoes_automaticas: h.simulacoes_automaticas.filter(simulacao => simulacao.simulacao_id !== simulacaoId),
          simulacoes_manuais: h.simulacoes_manuais.filter(simulacao => simulacao.simulacao_id !== simulacaoId),
        }))
      );
    } catch (error) {
      setError(error.message);
    }
  };

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (error) {
    return <div>Erro: {error}</div>;
  }

  return (
    <div className="historico-container">
      <h1>Histórico de Simulações</h1>
      <div className="historico-list">
        {historico.map(item => (
          <div key={item.id}>
            <div className="simulacoes-tipo">
              <h2>Simulações Automáticas</h2>
              <div className="simulacoes-grid">
                {Array.isArray(item.simulacoes_automaticas) && item.simulacoes_automaticas.map(simulacao => (
                  <div key={simulacao.simulacao_id} className="simulacao-card">
                    <h3>{simulacao.nome}</h3>
                    <p>Data Inicial: {simulacao.data_inicial}</p>
                    <p>Data Final: {simulacao.data_final}</p>
                    <p>Aplicação Inicial: {simulacao.aplicacao_inicial}</p>
                    <p>Aplicação Mensal: {simulacao.aplicacao_mensal}</p>
                    <Link to={`/abrirsimulacaoautomatica/${simulacao.simulacao_id}`} className="open-simulacao-link">
                      Abrir Simulação
                    </Link>
                    <button onClick={() => handleDeleteAutomatica(simulacao.simulacao_id)}>Excluir</button>
                  </div>
                ))}
              </div>
            </div>

            <div className="simulacoes-tipo">
              <h2>Simulações Manuais</h2>
              <div className="simulacoes-grid">
                {Array.isArray(item.simulacoes_manuais) && item.simulacoes_manuais.map(simulacao => (
                  <div key={simulacao.simulacao_id} className="simulacao-card">
                    <h3>{simulacao.nome}</h3>
                    <p>Data Inicial: {simulacao.data_inicial}</p>
                    <p>Valor Total da Carteira: {simulacao.valor_total_carteira}</p>
                    <button
                      className="open-simulacao-link"
                      onClick={() => navigate('/simulacaomanual', { state: { simulacaoId: simulacao.simulacao_id, carteiraId: simulacao.carteira_id } })}
                    >
                      Abrir Simulação
                    </button>

                    <button onClick={() => handleDeleteManual(simulacao.simulacao_id)}>Excluir</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Historico;
