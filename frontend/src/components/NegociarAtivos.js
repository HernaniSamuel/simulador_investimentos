import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import Highcharts from 'highcharts/highstock';
import HighchartsReact from 'highcharts-react-official';
import indicatorsAll from 'highcharts/indicators/indicators-all';
import annotationsAdvanced from 'highcharts/modules/annotations-advanced';
import priceIndicator from 'highcharts/modules/price-indicator';
import fullScreen from 'highcharts/modules/full-screen';
import '../styles/NegociarAtivos.css';

// Inicialize os módulos adicionais do Highcharts
indicatorsAll(Highcharts);
annotationsAdvanced(Highcharts);
priceIndicator(Highcharts);
fullScreen(Highcharts);

const NegociarAtivos = () => {
  const location = useLocation();
  const { simulacaoId, ticker } = location.state || {};
  const [candlestickData, setCandlestickData] = useState([]);
  const [dinheiroDisponivel, setDinheiroDisponivel] = useState(0);
  const [valor, setValor] = useState('');
  const chartRef = useRef(null);

  useEffect(() => {
    if (simulacaoId && ticker) {
      fetchDadosSimulacao(simulacaoId, ticker);
    }
  }, [simulacaoId, ticker]);

  const fetchDadosSimulacao = async (simulacaoId, ticker) => {
    if (!ticker || !simulacaoId) {
      console.error('Ticker ou Simulação ID não fornecidos.');
      return;
    }
  
    try {
      console.log('Enviando requisição com:', { simulacaoId, ticker });
      const response = await fetch(`http://127.0.0.1:8000/api/negociar_ativos/${simulacaoId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker })
      });
  
      const data = await response.json();
  
      if (response.ok) {
        console.log('Dados recebidos:', data);
        const historico = data.historico || [];
        const processedData = historico.map(item => [
          new Date(item.date).getTime(),
          parseFloat(item.open),
          parseFloat(item.high),
          parseFloat(item.low),
          parseFloat(item.close)
        ]);
        console.log('Dados processados para o gráfico:', processedData);
        setCandlestickData(processedData);
        setDinheiroDisponivel(data.dinheiro_em_caixa || 0);
      } else {
        console.error('Erro ao buscar dados da simulação:', data.error || 'Erro desconhecido');
      }
    } catch (error) {
      console.error('Erro ao buscar dados do gráfico de velas:', error);
    }
  };

  const handleCompra = () => {
    console.log(`Comprando com valor de R$ ${valor} de ${ticker}`);
  };

  const handleVenda = () => {
    console.log(`Vendendo com valor de R$ ${valor} de ${ticker}`);
  };

  const options = {
    chart: {
      type: 'candlestick',
      height: '500px'
    },
    rangeSelector: {
      selected: 1,
      buttons: [
        { type: 'day', count: 1, text: '1d' },
        { type: 'week', count: 1, text: '1w' },
        { type: 'month', count: 1, text: '1m' },
        { type: 'month', count: 3, text: '3m' },
        { type: 'year', count: 1, text: '1y' },
        { type: 'all', text: 'All' }
      ]
    },
    title: {
      text: `Gráfico de Velas - ${ticker}`
    },
    series: [{
      type: 'candlestick',
      name: ticker,
      data: candlestickData,
      tooltip: {
        valueDecimals: 2
      }
    }],
    yAxis: [{
      labels: { align: 'right', x: -3 },
      height: '100%',
      lineWidth: 2,
      resize: { enabled: true }
    }],
    tooltip: { split: true },
    responsive: {
      rules: [{
        condition: { maxWidth: 800 },
        chartOptions: { rangeSelector: { inputEnabled: false } }
      }]
    }
  };

  return (
    <div className="negociar-ativos-container">
      <div className="controles-container">
        <h3>{ticker}</h3>
        <span>Dinheiro: R$ {dinheiroDisponivel.toFixed(2)}</span>
        <input
          type="number"
          placeholder="Valor"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="input-valor"
        />
        <button className="botao-compra" onClick={handleCompra}>Comprar</button>
        <button className="botao-venda" onClick={handleVenda}>Vender</button>
      </div>
      <div className="grafico-container">
        <HighchartsReact
          highcharts={Highcharts}
          constructorType={'stockChart'}
          options={options}
          ref={chartRef}
        />
      </div>
    </div>
  );
};

export default NegociarAtivos;