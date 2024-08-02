import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

function ResultadoSimulacaoAutomatica() {
  const location = useLocation();
  const { simulacaoId } = location.state || {};

  const [loading, setLoading] = useState(true);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://127.0.0.1:8000/api/resultado_simulacao_automatica/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ simulacao_id: simulacaoId })
        });

        if (!response.ok) {
          throw new Error('Erro ao buscar os resultados da simulação');
        }

        const data = await response.json();
        setResultado(data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [simulacaoId]);

  return (
    <div>
      {loading && <p>A simulação está sendo executada, por favor aguarde...</p>}
      {!loading && error && <p>Erro: {error}</p>}
      {!loading && resultado && (
        <div>
          <h1>Resultado da Simulação</h1>
          <p>{JSON.stringify(resultado)}</p>
        </div>
      )}
    </div>
  );
}

export default ResultadoSimulacaoAutomatica;
