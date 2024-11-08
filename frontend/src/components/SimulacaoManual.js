import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Highcharts from 'highcharts/highstock';
import HighchartsReact from 'highcharts-react-official';
import config from '../config';

import '../styles/SimulacaoManual.css';

const SimulacaoManual = () => {
  const location = useLocation();
  const { simulacaoId } = location.state || {};

  const [ajustarPoderCompra, setAjustarPoderCompra] = useState(false);
  const [valor, setValor] = useState('');
  const [dinheiroEmCaixa, setDinheiroEmCaixa] = useState(0.0);
  const [dataAtual, setDataAtual] = useState('');
  const [lineData, setLineData] = useState([]);
  const [pieData, setPieData] = useState([]);
  const [nomeSimulacao, setNomeSimulacao] = useState('');  // Novo estado para armazenar o nome da simulação

  const navigate = useNavigate();

  useEffect(() => {
    if (simulacaoId) {
      fetchSimulacaoData();
    }
  }, [simulacaoId]);

  const fetchSimulacaoData = async () => {
    try {
      const response = await fetch(
        `${config}/api/simulacao_manual/${simulacaoId}/`
      );
      const data = await response.json();
  
      if (response.ok) {
        setDinheiroEmCaixa(data.cash);
        setDataAtual(data.mes_atual);
        setLineData(data.lineData.valorTotal || []);
        setPieData(data.pieData);
        setNomeSimulacao(data.nome_simulacao || '');
      } else {
        alert(data.error || 'Erro ao buscar dados da simulação.');
      }
    } catch (error) {
      console.error('Erro ao buscar dados da simulação:', error);
      alert('Ocorreu um erro ao buscar os dados da simulação. Tente novamente.');
    }
  };

  const handleCheckboxChange = (e) => {
    setAjustarPoderCompra(e.target.checked);
  };

  const handleValorChange = (e) => {
    setValor(e.target.value);
  };

  const handleAdicionarDinheiro = async () => {
    if (!simulacaoId) {
      alert('ID da simulação não encontrado.');
      return;
    }

    try {
      const response = await fetch(
        `${config}/api/modificar_dinheiro/${simulacaoId}/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            valor: parseFloat(valor),
            ajustarInflacao: ajustarPoderCompra,
          }),
        }
      );

      const data = await response.json();

      if (response.ok && data.novo_valor !== undefined) {
        setDinheiroEmCaixa(data.novo_valor);
        setValor(''); // Limpa o campo após a adição
      } else if (data.error) {
        alert(data.error);
      } else if (data.message) {
        alert(data.message);
      }
    } catch (error) {
      console.error('Erro ao adicionar dinheiro:', error);
      alert('Ocorreu um erro ao adicionar o dinheiro. Tente novamente.');
    }
  };

  const handleAvancarMes = async () => {
    if (!simulacaoId) {
      alert('ID da simulação não encontrado.');
      return;
    }
  
    try {
      const response = await fetch(
        `${config}/api/avancar_mes/${simulacaoId}/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
  
      const data = await response.json();
  
      if (response.ok && data.mes_atual) {
        setDataAtual(data.mes_atual);
        await fetchSimulacaoData(); // Fetch updated data
      } else if (data.error) {
        alert(data.error);
      } else if (data.message) {
        alert(data.message);
      }
    } catch (error) {
      console.error('Erro ao avançar o mês:', error);
      alert('Ocorreu um erro ao avançar o mês. Tente novamente.');
    }
  };
  

  const formatarData = (dataString) => {
    const partes = dataString.split('-');
    if (partes.length !== 3) {
      return dataString;
    }
    const [ano, mes, dia] = partes;
    return `${dia}/${mes}/${ano}`;
  };

  const lineOptions = {
    chart: {
      height: null,
      width: null,
    },
    title: {
      text: 'Valor Total da Carteira',
    },
    xAxis: {
      categories: lineData.map((_, index) => `Mês ${index + 1}`),
    },
    series: [
      {
        name: 'Valor Total',
        data: lineData,
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
        name: 'Peso',
        data: pieData,
      },
    ],
  };

  return (
    <div className="dashboard">
      <div className="header-placeholder"></div>

      {/* Adiciona o título com o nome da simulação */}
      {nomeSimulacao && <h1 className="titulo-simulacao">{nomeSimulacao}</h1>}

      <div className="line-chart-section">
        <div className="controls">
          <div className="compact-controls">
            <span>Dinheiro em caixa: R${dinheiroEmCaixa}</span>
            <input
              type="number"
              placeholder="Valor"
              value={valor}
              onChange={handleValorChange}
            />
            <label>
              <input
                type="checkbox"
                checked={ajustarPoderCompra}
                onChange={handleCheckboxChange}
              />
              Ajustar poder de compra
            </label>
            <button onClick={handleAdicionarDinheiro}>Adicionar mais dinheiro</button>
          </div>
          <Link
            className='link'
            to={{
              pathname: '/negociarativospesquisa',
            }}
            state={{ simulacaoId }} // Certifique-se de que simulacaoId tenha um valor válido aqui
          >
            Negociar Ativos
          </Link>
          <span>{dataAtual ? formatarData(dataAtual) : ''}</span>
          <button onClick={handleAvancarMes}>Próximo Mês</button>
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
                  <th>Peso</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                {pieData.map((ativo, index) => (
                  <tr key={index}>
                    <td>{ativo.name}</td>
                    <td>{ativo.y}%</td>
                    <td>
                      <button
                        onClick={() => navigate(`/negociarativos`, { state: { simulacaoId, ticker: ativo.name } })}
                      >
                        Negociar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulacaoManual;
