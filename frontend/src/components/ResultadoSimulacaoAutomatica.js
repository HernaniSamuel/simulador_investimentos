import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';

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
        console.log("Dados recebidos:", data); // Mostra os dados no console
        setResultado(data);
      } catch (error) {
        console.error("Erro ao buscar dados:", error); // Mostra erros no console
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [simulacaoId]);

  // Configuração do gráfico
  const chartOptions = resultado
    ? {
        title: {
          text: 'Resultado da Simulação Automática'
        },
        xAxis: {
          categories: resultado.dates, // Supondo que você tenha uma lista de datas no resultado
          title: {
            text: 'Meses'
          }
        },
        yAxis: {
          title: {
            text: 'Valor da Carteira (BRL)'
          }
        },
        series: [
          {
            name: 'Valor da Carteira',
            data: resultado.adjclose_carteira // Supondo que os valores ajustados da carteira estejam aqui
          }
        ]
      }
    : null;

  return (
    <div>
      {loading && <p>A simulação está sendo executada, por favor aguarde...</p>}
      {!loading && error && <p>Erro: {error}</p>}
      {!loading && resultado && (
        <div>
          <h1>Resultado da Simulação</h1>
          <HighchartsReact highcharts={Highcharts} options={chartOptions} />
          <pre>{JSON.stringify(resultado, null, 2)}</pre> {/* Mostra os dados formatados na tela */}
        </div>
      )}
    </div>
  );
}

export default ResultadoSimulacaoAutomatica;
