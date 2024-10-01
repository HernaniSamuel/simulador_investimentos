import React from 'react';
import Highcharts from 'highcharts/highstock';
import HighchartsReact from 'highcharts-react-official';
import '../styles/SimulacaoManual.css';

const Dashboard = () => {
  // Opções para o gráfico de linhas (Highcharts)
  const lineOptions = {
    chart: {
      height: null, // Permite que o gráfico ocupe 100% da altura do contêiner
      width: null,
    },
    title: {
      text: 'Valor Total da Carteira'
    },
    xAxis: {
      categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    },
    series: [
      {
        name: 'Valor Total',
        data: [1200, 1500, 1300, 1700, 1900, 2200],
        color: '#4CAF50',
      }
    ]
  };

  // Opções para o gráfico de setores (Highcharts)
  const pieOptions = {
    chart: {
      type: 'pie',
      height: null,
    },
    title: {
      text: 'Distribuição de Ativos'
    },
    series: [
      {
        name: 'Ativos',
        data: [
          { name: 'Ação 1', y: 40, color: '#FF6384' },
          { name: 'Ação 2', y: 20, color: '#36A2EB' },
          { name: 'Ação 3', y: 30, color: '#FFCE56' },
          { name: 'Ação 4', y: 10, color: '#4CAF50' }
        ]
      }
    ]
  };

  return (
    <div className="dashboard">
      {/* Espaço para o header (20% da altura da tela) */}
      <div className="header-placeholder"></div>

      {/* Seção do gráfico de linhas */}
      <div className="line-chart-section">
        <div className="controls">
          <button>Adicionar mais dinheiro</button>
          <input type="number" placeholder="Valor" />
          <button>Ajustar poder de compra</button>
          <button>Próximo Mês</button>
        </div>
        <div class="chart-container">
            <div className="line-chart">
                <HighchartsReact highcharts={Highcharts} options={lineOptions} />
            </div>
        </div>

      </div>

      {/* Seção inferior */}
      <div className="bottom-section">
        <div className="charts-info-container">
          {/* Gráfico de pizza à esquerda */}
          <div className="pie-chart-container">
            <HighchartsReact highcharts={Highcharts} options={pieOptions} />
          </div>
          {/* Tabela de distribuição de ativos à direita */}
          <div className="info-table">
            <h3>Distribuição de Ativos</h3>
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Peso %</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>IVV</td>
                  <td>42%</td>
                  <td><button>Negociar</button></td>
                </tr>
                {/* Adicionar mais linhas conforme necessário */}
              </tbody>
            </table>
          </div>
        </div>
        {/* Indicadores de performance abaixo */}
        <div className="performance-indicators">
          <h3>Indicadores de Performance</h3>
          <p>Você pode colocar informações adicionais de performance aqui.</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
