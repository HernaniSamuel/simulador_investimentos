// src/components/DataComponent.js
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import FormComponent from './FormComponent';
import CandlestickChart from './CandlestickChart';
import '../styles/DataComponent.css';

const DataComponent = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ticker, setTicker] = useState('');

  const handleFormSubmit = (formData) => {
    setLoading(true);
    setTicker(formData.ticker);
    fetch('http://127.0.0.1:8000/api/getdata', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    })
      .then(response => response.json())
      .then(data => {
        console.log(data); // Verifique os dados no console
        setData(data);
        setLoading(false);
      })
      .catch(error => {
        setError(error);
        setLoading(false);
      });
  };

  return (
    <div className="container">
      <h1>Dados do Ativo</h1>
      <FormComponent onSubmit={handleFormSubmit} />
      {loading && <p className="message">Loading...</p>}
      {error && <p className="message error">Error: {error.message}</p>}
      {data.length > 0 && (
        <div className="chart-container">
          <CandlestickChart data={data} ticker={ticker} />
        </div>
      )}
      <div className="back-link-container">
        <Link className="back-link" to='/'>Voltar ao início da aplicação</Link>
      </div>
    </div>
  );
};

export default DataComponent;
