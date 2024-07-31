from django.http import JsonResponse
import yfinance as yf


def pesquisar_precos(ticker, data_inicial, data_final):
    """
    Pesquisa os preços do ativo usando yfinance.
    """
    data_inicio = data_inicial.strftime('%Y-%m-%d')
    data_fim = data_final.strftime('%Y-%m-%d')
    dados = yf.download(ticker, start=data_inicio, end=data_fim, interval='1mo')
    return dados
