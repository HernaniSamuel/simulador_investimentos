import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './components/App';
import reportWebVitals from './reportWebVitals';

import { createBrowserRouter, RouterProvider } from 'react-router-dom';

//Importar componentes
import NovaSimulacaoAutomatica from './components/NovaSimulacaoAutomatica';
import SelecionarAtivosAutomatica from './components/SelecionarAtivosAutomatica';
import Historico from './components/Historico';
import ResultadoSimulacaoAutomatica from './components/ResultadoSimulacaoAutomatica';
import AbrirSimulacaoAutomatica from './components/AbrirSimulacaoAutomatica';
import NovaSimulacaoManual from './components/NovaSimulacaoManual';
import SimulacaoManual from './components/SimulacaoManual';
import NegociarAtivosPesquisa from './components/NegociarAtivosPesquisa';
import NegociarAtivos from './components/NegociarAtivos';


const router = createBrowserRouter([
  {
    path:"/",
    element: <App/>,
    children: [
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
        {
          path:"/resultadosimulacaoautomatica",
          element: <ResultadoSimulacaoAutomatica/>
        },
        {
          path:"/abrirsimulacaoautomatica/:simulacaoId",
          element: <AbrirSimulacaoAutomatica/>
        },
        {
          path:"/novasimulacaomanual",
          element: <NovaSimulacaoManual/>
        },
        {
          path:"/simulacaomanual",
          element: <SimulacaoManual/>
        },
        {
          path:"/negociarativospesquisa",
          element: <NegociarAtivosPesquisa/>
        },
        {
          path:"/negociarativos",
          element: <NegociarAtivos/>
        },
    ]
  }
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
