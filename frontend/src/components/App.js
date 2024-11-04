import React, { useState, useEffect } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import '../styles/App.css';
import imagemReversao from '../images/regressao_poder_compra.png';
import imagemValorCompra from '../images/formula_valor_compra.png';
import imagemFormulaCompra from '../images/formula_compra_ativos.png';
import imagemValorTotal from '../images/descobrir_valor_total.png';



function App() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showTutorial, setShowTutorial] = useState(true);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  // Obter a localização atual para verificar a rota
  const location = useLocation();

  // Atualizar o estado do tutorial com base na rota atual
  useEffect(() => {
    // Mostrar tutorial apenas na rota inicial '/'
    if (location.pathname === '/') {
      setShowTutorial(true);
    } else {
      setShowTutorial(false);
    }
  }, [location]);

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
        {showTutorial && (
          <div className="tutorial">
            <h1>Tutorial da Simulação Automática</h1>
            <p>A simulação automática foi projetada para ser rápida e prática, automatizando a compra de ativos, o reinvestimento de dividendos e o rebalanceamento da carteira. No entanto, essa abordagem sacrifica a precisão — devido à lógica de compra fragmentada, que nem sempre é viável no cenário real — e não permite a venda de ativos, uma vez que todo o processo é automatizado.</p>

            <div className="video-wrapper">
              <iframe
                src="https://www.youtube.com/embed/aquSCTMMcvY?si=9QkWePuHZcRCqrPr"
                title="YouTube video player"

                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerPolicy="strict-origin-when-cross-origin"
                allowFullScreen
              ></iframe>
            </div>
            <h2>Detalhes técnicos</h2>
            <img src={imagemReversao} alt="Descrição da imagem" className="responsive-image" />
            <img src={imagemValorCompra} alt="Descrição da imagem" className="responsive-image" />
            <img src={imagemFormulaCompra} alt="Descrição da imagem" className="responsive-image" />
            <img src={imagemValorTotal} alt="Descrição da imagem" className="responsive-image" />
            <div className='texto'>
            <h3>Compra fragmentada e rebalanceamento automático</h3>
            <p>Devido à lógica de compra fragmentada, que resulta na posse de ativos com várias casas decimais, o rebalanceamento da carteira de ações ocorre de forma automática e com precisão total a cada mês de simulação, eliminando a necessidade de ajustes manuais. Os dividendos são incorporados diretamente ao preço do ativo, refletindo seu impacto no valor total da carteira.</p>
            </div>
            
            {/* Conteúdo do tutorial */}

          </div>
        )}
        <Outlet />
      </main>
    </div>
  );
}

export default App;
