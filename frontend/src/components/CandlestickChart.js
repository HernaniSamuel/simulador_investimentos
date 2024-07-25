// src/components/CandlestickChart.js
import React from 'react';
import Highcharts from 'highcharts/highstock';
import HighchartsReact from 'highcharts-react-official';

const CandlestickChart = ({ data, ticker }) => {
  const formattedData = data.map(item => [
    new Date(item.Date).getTime(),
    item.Open,
    item.High,
    item.Low,
    item.Close,
  ]);

  const options = {
    title: {
      text: `Gráfico de Velas - ${ticker}`
    },
    series: [
      {
        type: 'candlestick',
        name: ticker,
        data: formattedData,
        color: '#f00',
        upColor: '#0f0',
      },
    ],
    xAxis: {
      type: 'datetime',
    },
  };

  return <HighchartsReact highcharts={Highcharts} constructorType={'stockChart'} options={options} />;
};

export default CandlestickChart;
