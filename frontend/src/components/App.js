import { Link, Outlet } from 'react-router-dom';
import '../styles/App.css'; // Certifique-se de que este arquivo de estilo contém os estilos atualizados

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <nav className="navbar">
          <Link to="/" className="nav-link">Início</Link>
          <Link to="/novasimulacaoautomatica" className="nav-link">Nova Simulação Automática</Link>
          <Link to="/historico" className="nav-link">Histórico de Simulações</Link>
          <Link to="/getdata" className="nav-link">Ver ativo</Link>
        </nav>
      </header>
      <main>
        <Outlet /> {/* Este é o local onde o conteúdo das rotas será renderizado */}
      </main>
    </div>
  );
}

export default App;
