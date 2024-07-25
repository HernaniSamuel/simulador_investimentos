// src/components/FormComponent.js
import React, { useState } from 'react';
import '../styles/FormComponent.css';

const FormComponent = ({ onSubmit }) => {
  const [ticker, setTicker] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [interval, setInterval] = useState('1d');

  const handleSubmit = (event) => {
    event.preventDefault();

    // Formatar as datas para o formato AAAA-MM-DD
    const formattedStartDate = new Date(startDate).toISOString().split('T')[0];
    const formattedEndDate = new Date(endDate).toISOString().split('T')[0];

    onSubmit({
      ticker: ticker,
      start_date: formattedStartDate,
      end_date: formattedEndDate,
      interval: interval,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        <span>Ticker:</span>
        <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value)} />
      </label>
      <label>
        <span>Data de Início:</span>
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
      </label>
      <label>
        <span>Data de Fim:</span>
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      </label>
      <label>
        <span>Intervalo:</span>
        <select value={interval} onChange={(e) => setInterval(e.target.value)}>
          <option value="1m">1 minuto</option>
          <option value="2m">2 minutos</option>
          <option value="5m">5 minutos</option>
          <option value="15m">15 minutos</option>
          <option value="30m">30 minutos</option>
          <option value="60m">1 hora</option>
          <option value="90m">90 minutos</option>
          <option value="1h">1 hora</option>
          <option value="1d">1 dia</option>
          <option value="5d">5 dias</option>
          <option value="1wk">1 semana</option>
          <option value="1mo">1 mês</option>
          <option value="3mo">3 meses</option>
        </select>
      </label>
      <button type="submit">Buscar Dados</button>
    </form>
  );
};

export default FormComponent;
