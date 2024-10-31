import React, { useState } from 'react';
import { Link, Outlet } from 'react-router-dom';
import '../styles/App.css';

function App() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="hamburger-menu" onClick={toggleMenu}>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </div>
        <nav className={`navbar ${isMenuOpen ? 'open' : ''}`}>
          <Link to="/" className="nav-link" onClick={closeMenu}>Início</Link>
          <Link to="/novasimulacaoautomatica" className="nav-link" onClick={closeMenu}>Nova Simulação Automática</Link>
          <Link to="/novasimulacaomanual" className="nav-link" onClick={closeMenu}>Nova Simulação Manual</Link>
          <Link to="/historico" className="nav-link" onClick={closeMenu}>Histórico de Simulações</Link>
          <a className="nav-link" href="http://127.0.0.1:8000/account/logout/">Logout</a>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default App;
