import React, { useState, useEffect, useRef, useMemo } from 'react';
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

  const [precoConvertido, setPrecoConvertido] = useState(0);
  const [moedaAtivo, setMoedaAtivo] = useState('');
  const [moedaCarteira, setMoedaCarteira] = useState('');
  const [quantidadeAtivo, setQuantidadeAtivo] = useState(0); // Definido o estado para a quantidade de ativos

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
        const { historico, dinheiro_em_caixa, preco_convertido, moeda_ativo, moeda_carteira, quantidade_ativo } = data;

        const processedData = historico.map(item => [
          new Date(item.date).getTime(),
          parseFloat(item.open),
          parseFloat(item.high),
          parseFloat(item.low),
          parseFloat(item.close)
        ]);

        setCandlestickData(processedData);
        setDinheiroDisponivel(dinheiro_em_caixa || 0);
        setPrecoConvertido(preco_convertido);
        setMoedaAtivo(moeda_ativo);
        setMoedaCarteira(moeda_carteira);
        setQuantidadeAtivo(quantidade_ativo);  // Atualiza a quantidade de ativos
      } else {
        console.error('Erro ao buscar dados da simulação:', data.error || 'Erro desconhecido');
      }

    } catch (error) {
      console.error('Erro ao buscar dados do gráfico de velas:', error);
    }
  };

  const handleCompraVenda = async (tipoOperacao) => {
    const valorNumerico = parseFloat(valor);
  
    // Verifica se o valor é maior que 0
    if (!valorNumerico || valorNumerico <= 0) {
      alert('Por favor, insira um valor válido.');
      return;
    }
  
    // Verifica se é uma compra e se há dinheiro suficiente
    if (tipoOperacao === 'compra' && valorNumerico > dinheiroDisponivel) {
      alert('Saldo insuficiente para compra.');
      return;
    }
  
    // Verifica se é uma venda e se há ativos suficientes na carteira
    const valorVenda = valorNumerico / precoConvertido; // Calcula a quantidade de ativos a vender
    if (tipoOperacao === 'venda' && valorVenda > quantidadeAtivo) {
      alert('Você não possui ativos suficientes para venda.');
      return;
    }
  
    // Se tudo estiver correto, faz a requisição para o backend
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/buy_sell_actives/${simulacaoId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tipo: tipoOperacao,
          valor: valorNumerico,
          precoConvertido: precoConvertido,
          ticker: ticker  // Envia o ticker que está sendo negociado
        })
      });
  
      const data = await response.json();
  
      if (response.ok) {
        alert(`${tipoOperacao === 'compra' ? 'Compra' : 'Venda'} realizada com sucesso!`);
        // Atualiza os valores após a transação
        setDinheiroDisponivel(data.novoDinheiroDisponivel);
        setQuantidadeAtivo(data.novaQuantidadeAtivo);  // Atualiza a quantidade de ativos na carteira
      } else {
        alert(`Erro ao realizar a ${tipoOperacao}. Tente novamente.`);
      }
    } catch (error) {
      console.error('Erro ao realizar a transação:', error);
      alert('Erro ao realizar a transação. Tente novamente.');
    }
  };
  
  const options = useMemo(() => ({
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
      name: ticker || 'Dados Padrão',
      data: candlestickData,
      color: '#dc3545',
      upColor: '#28a745',
      lineColor: '#000000',
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
  }), [candlestickData, ticker]);

  return (
    <div className="negociar-ativos-container">
      <div className="controles-container">
        <h3>{ticker}</h3>
        <span>Dinheiro: {moedaCarteira} {dinheiroDisponivel.toFixed(2)}</span>

        <input
          type="number"
          placeholder="Valor na moeda base da carteira"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="input-valor"
        />
        {moedaAtivo !== moedaCarteira && (
          <p>Preço convertido: {precoConvertido.toFixed(2)} {moedaCarteira}</p>
        )}

        <button className="botao-compra" onClick={() => handleCompraVenda('compra')}>Comprar</button>
        <button className="botao-venda" onClick={() => handleCompraVenda('venda')}>Vender</button>

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
