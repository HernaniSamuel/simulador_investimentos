from datetime import datetime, timedelta
import yfinance as yf


def pesquisar_ativo_por_ticker(ticker):
    if not ticker:
        return {'error': 'Ticker is required'}, 400

    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        # Verificando se o ticker é válido
        if 'longName' in stock_info:
            stock_name = stock_info['longName']
        else:
            stock_name = 'Unknown'

        # Definindo o período para obter os dados históricos do ticker
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # Baixa os dados do ativo com intervalo diário
        stock_data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

        # Verificando se há dados retornados
        if not stock_data.empty:
            adj_close = stock_data['Adj Close'].iloc[-1]  # Último valor de 'Adj Close'
            if adj_close > 0:
                return {'exists': True, 'ticker': ticker, 'name': stock_name}, 200
            else:
                return {'exists': False, 'ticker': ticker, 'name': stock_name}, 404
        else:
            return {'exists': False, 'ticker': ticker, 'name': stock_name}, 404
    except Exception as e:
        print(f"Error checking ticker: {e}")
        return {'exists': False, 'ticker': ticker, 'error': str(e)}, 500
