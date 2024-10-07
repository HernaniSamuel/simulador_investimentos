import React, { useState } from 'react';
import Highcharts from 'highcharts/highstock';
import HighchartsReact from 'highcharts-react-official';
import '../styles/SimulacaoManual.css';
import { Link } from 'react-router-dom';

const SimulacaoManual = () => {
  const [ajustarPoderCompra, setAjustarPoderCompra] = useState(false);

  const lineOptions = {
    chart: {
      height: null,
      width: null,
    },
    title: {
      text: 'Valor Total da Carteira',
    },
    xAxis: {
      categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    },
    series: [
      {
        name: 'Valor Total',
        data: [1200, 1500, 1300, 1700, 1900, 2200],
        color: '#4CAF50',
      },
    ],
  };

  const pieOptions = {
    chart: {
      type: 'pie',
      height: null,
    },
    title: {
      text: 'Distribuição de Ativos',
    },
    series: [
      {
        name: 'Ativos',
        data: [
          { name: 'IVV', y: 40, color: '#FF6384' },
          { name: 'MSFT', y: 20, color: '#36A2EB' },
          { name: 'AAPL', y: 30, color: '#FFCE56' },
          { name: 'NVDA', y: 10, color: '#4CAF50' },
        ],
      },
    ],
  };

  const handleCheckboxChange = (e) => {
    setAjustarPoderCompra(e.target.checked);
  };

  return (
    <div className="dashboard">
      <div className="header-placeholder"></div>

      <div className="line-chart-section">
        <div className="controls">
          <div className="compact-controls">
            <span>Dinheiro em caixa: R$10000</span>
            <button>Adicionar mais dinheiro</button>
            <input type="number" placeholder="Valor" />
            <label>
              <input
                type="checkbox"
                checked={ajustarPoderCompra}
                onChange={handleCheckboxChange}
              />
              Ajustar poder de compra
            </label>
          </div>
          <Link className='link' to='/historico' target='_blank'>Negociar Ativos</Link>
          <button>Próximo Mês</button>
        </div>
        <div className="chart-container">
          <div className="line-chart">
            <HighchartsReact highcharts={Highcharts} options={lineOptions} />
          </div>
        </div>
      </div>

      <div className="bottom-section">
        <div className="charts-info-container">
          <div className="pie-chart-container">
            <HighchartsReact highcharts={Highcharts} options={pieOptions} />
          </div>
          <div className="info-table">
            <h3>Distribuição de Ativos</h3>
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Posse</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>IVV</td>
                  <td>40x</td>
                  <td><button>Negociar</button></td>
                </tr>
                <tr>
                  <td>TSLA</td>
                  <td>30x</td>
                  <td><button>Negociar</button></td>
                </tr>
                <tr>
                  <td>MSFT</td>
                  <td>20x</td>
                  <td><button>Negociar</button></td>
                </tr>
                <tr>
                  <td>AAPL</td>
                  <td>10x</td>
                  <td><button>Negociar</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div className="performance-indicators">
          <h3>Indicadores de Performance</h3>
          <p>Você pode colocar informações adicionais de performance aqui.</p>
        </div>
      </div>
    </div>
  );
};

export default SimulacaoManual;