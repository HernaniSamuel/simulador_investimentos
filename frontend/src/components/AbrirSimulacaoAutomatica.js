import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';  // Alterado para usar useParams
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import '../styles/AbrirSimulacaoAutomatica.css';
import config from '../config'
function AbrirSimulacaoAutomatica() {
  const { simulacaoId } = useParams();  // Obtenha o simulacaoId diretamente da URL

  const [loading, setLoading] = useState(true);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${config.backendUrl}/api/abrir_simulacao_automatica/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ simulacao_id: simulacaoId })  // Enviando o simulacaoId no corpo da requisição
        });

        if (!response.ok) {
          throw new Error('Erro ao buscar os resultados da simulação');
        }

        const data = await response.json();
        setResultado(data);
      } catch (error) {
        console.error("Erro ao buscar dados:", error);  // Mostra erros no console
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [simulacaoId]);

  // Configuração do gráfico de linhas
  const chartOptions = resultado
    ? {
        title: {
          text: 'Valor da Carteira ao Longo do Tempo'
        },
        xAxis: {
          categories: resultado.resultado.map(entry => entry.Data),
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
            data: resultado.resultado.map(entry => entry.Valor)
          }
        ]
      }
    : null;

  // Configuração do gráfico de setores
  const pieChartOptions = resultado
    ? {
        chart: {
          type: 'pie'
        },
        title: {
          text: 'Distribuição dos Ativos'
        },
        series: [
          {
            name: 'Peso',
            data: resultado.simulacao.ativos.map(ativo => ({
              name: ativo.nome,
              y: ativo.peso * 100  // Convertendo para porcentagem
            }))
          }
        ]
      }
    : null;

  return (
    <div className="resultado-simulacao-container">
      {loading && <p>A simulação está sendo executada, por favor aguarde...</p>}
      {!loading && error && <p>Erro: {error}</p>}
      {!loading && resultado && (
        <div>
          <h1>{resultado.simulacao.nome || 'Resultado da Simulação'}</h1>
          <div className="charts-container">
            <div className="line-chart">
              <HighchartsReact highcharts={Highcharts} options={chartOptions} />
            </div>
            <div className="pie-chart">
              <HighchartsReact highcharts={Highcharts} options={pieChartOptions} />
            </div>
          </div>
          <div className="simulation-info">
            <p><strong>Valor Inicial:</strong> {resultado.simulacao.valor_inicial}</p>
            <p><strong>Valor Mensal:</strong> {resultado.simulacao.valor_mensal}</p>
            <p><strong>Data Inicial:</strong> {resultado.simulacao.data_inicial}</p>
            <p><strong>Data Final:</strong> {resultado.simulacao.data_final}</p>
            <h3>Ativos:</h3>
            <ul>
              {resultado.simulacao.ativos.map(ativo => (
                <li key={ativo.ticker}>
                  {ativo.nome} ({ativo.ticker}) - Peso: {ativo.peso}, Posse: {ativo.posse}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default AbrirSimulacaoAutomatica;
