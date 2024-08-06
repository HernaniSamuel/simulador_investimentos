import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './components/App';
import reportWebVitals from './reportWebVitals';

import { createBrowserRouter, RouterProvider } from 'react-router-dom';

//Importar componentes
import GetData from './components/DataComponent';
import NovaSimulacaoAutomatica from './components/NovaSimulacaoAutomatica';
import SelecionarAtivosAutomatica from './components/SelecionarAtivosAutomatica';
import Historico from './components/Historico';

//Estruturar rotas
const router = createBrowserRouter([
  {
    path:"/",
    element: <App/>
  },
  {
      path:"/getdata",
      element: <GetData/>
  },
  {
    path:"/novasimulacaoautomatica",
    element: <NovaSimulacaoAutomatica/>
  },
  {
    path:"/selecionarativosautomatica",
    element: <SelecionarAtivosAutomatica/>
  },
  {
    path:"/historico",
    element: <Historico/>
  },
])

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
