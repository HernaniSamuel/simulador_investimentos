import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import PesquisarAtivo from './PesquisarAtivo';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import '../styles/SelecionarAtivosAutomatica.css';
import config from '../config';


function SelecionarAtivosAutomatica() {
  const [ativos, setAtivos] = useState([]);
  const [pesos, setPesos] = useState({});
  const navigate = useNavigate();
  const location = useLocation();
  const { simulacaoId, carteiraId } = location.state || {};

  useEffect(() => {
    if (!simulacaoId || !carteiraId) {
      alert('Simulação ou carteira não encontrada.');
      navigate('/');
    }
  }, [simulacaoId, carteiraId, navigate]);

  const arredondarPeso = (peso, casasDecimais) => {
    const fator = Math.pow(10, casasDecimais);
    return Math.round(peso * fator) / fator;
  };

  const adicionarAtivo = (ticker) => {
    if (!ativos.includes(ticker)) {
      const novosPesos = { ...pesos, [ticker]: 100 };
      const somaPesos = Object.values(novosPesos).reduce((acc, peso) => acc + peso, 0);
      const fatorAjuste = 100 / somaPesos;

      const pesosAjustados = Object.keys(novosPesos).reduce((acc, ativo) => {
        acc[ativo] = arredondarPeso(novosPesos[ativo] * fatorAjuste, 2);
        return acc;
      }, {});

      setAtivos([...ativos, ticker]);
      setPesos(pesosAjustados);
    }
  };

  const removerAtivo = (ticker) => {
    setAtivos(ativos.filter(ativo => ativo !== ticker));
    const { [ticker]: _, ...rest } = pesos;
    setPesos(rest);
  };

  const atualizarPeso = (ticker, novoPeso) => {
    novoPeso = arredondarPeso(parseFloat(novoPeso), 2);  // Arredonda para duas casas decimais
    if (novoPeso > 100) novoPeso = 100;
    if (novoPeso < 0) novoPeso = 0;

    const outrosPesos = ativos.filter(ativo => ativo !== ticker);
    const somaOutrosPesos = outrosPesos.reduce((acc, ativo) => acc + pesos[ativo], 0);

    if (somaOutrosPesos + novoPeso > 100) {
      const fatorAjuste = arredondarPeso((100 - novoPeso) / somaOutrosPesos, 2);
      const novosPesos = outrosPesos.reduce((acc, ativo) => {
        acc[ativo] = arredondarPeso(pesos[ativo] * fatorAjuste, 2);
        return acc;
      }, { [ticker]: novoPeso });

      setPesos(novosPesos);
    } else {
      setPesos({ ...pesos, [ticker]: novoPeso });
    }
  };

  const handlePesoChange = (ticker, value) => {
    const parsedValue = parseFloat(value);
    if (!isNaN(parsedValue)) {
      atualizarPeso(ticker, parsedValue);
    }
  };

  const ajustarPesosProporcionalmente = () => {
    const somaPesos = Object.values(pesos).reduce((acc, peso) => acc + peso, 0);
    if (somaPesos !== 100) {
      const fatorAjuste = 100 / somaPesos;
      const pesosAjustados = Object.keys(pesos).reduce((acc, ativo) => {
        acc[ativo] = arredondarPeso(pesos[ativo] * fatorAjuste, 2);
        return acc;
      }, {});
      setPesos(pesosAjustados);
    }
  };

  const enviarDados = async () => {
    ajustarPesosProporcionalmente();

    const payload = {
      simulacao_id: simulacaoId,
      carteira_id: carteiraId,
      ativos: ativos
        .filter(ativo => pesos[ativo] > 0) // Filtra ativos com peso maior que 0
        .map(ativo => ({
          ticker: ativo,
          peso: arredondarPeso(pesos[ativo] / 100, 4) // Divide por 100 e arredonda para 4 casas decimais
        }))
    };

    try {
      const response = await fetch(`${config.backendUrl}/api/enviar_ativos/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        navigate('/resultadosimulacaoautomatica', { state: { simulacaoId } });
      } else {
        // Handle error response
        alert('Erro ao enviar os dados');
      }
    } catch (error) {
      // Handle network or other errors
      console.error('Erro ao enviar os dados:', error);
      alert('Erro ao enviar os dados');
    }
  };

  const data = ativos.map((ativo) => ({
    name: ativo,
    y: pesos[ativo] || 0
  }));

  const options = {
    chart: {
      type: 'pie'
    },
    title: {
      text: 'Distribuição dos Ativos'
    },
    series: [{
      name: 'Peso',
      data
    }]
  };

  return (
    <div className="selecionar-ativos-automatica-container">
      <h1>Selecionar Ativos e Definir Pesos</h1>
      <div className="top-section">
        <PesquisarAtivo adicionarAtivo={adicionarAtivo} />
        <div className="grafico-setores">
          <HighchartsReact
            highcharts={Highcharts}
            options={options}
          />
        </div>
      </div>
      <div className="lista-ativos">
        <h2>Ver ativos e definir pesos</h2>
        {ativos.map((ativo, index) => (
          <div key={index} className="ativo-item">
            <span>{ativo}</span>
            <div className="peso">
              <input
                type="number"
                value={pesos[ativo].toFixed(1)}
                onChange={(e) => handlePesoChange(ativo, e.target.value)}
                onBlur={() => {
                  // Arredonda o valor para uma casa decimal ao perder o foco
                  handlePesoChange(ativo, parseFloat(pesos[ativo].toFixed(1)));
                }}
                min="0"
                max="100"
              />
              <span>%</span>
              <input
                type="range"
                min="0"
                max="100"
                value={pesos[ativo]}
                onChange={(e) => atualizarPeso(ativo, parseFloat(e.target.value))}
              />
            </div>
            <button onClick={() => removerAtivo(ativo)} className="remover-button">Remover</button>
          </div>
        ))}
        <button onClick={enviarDados} className="enviar-button">Enviar Dados</button>
      </div>
    </div>
  );
}

export default SelecionarAtivosAutomatica;
