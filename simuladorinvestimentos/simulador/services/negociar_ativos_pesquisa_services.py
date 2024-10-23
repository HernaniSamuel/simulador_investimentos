import yfinance as yf
from django.shortcuts import get_object_or_404
from ..models import SimulacaoManual
from datetime import datetime


def pesquisar_ativo(ticker, simulacao_id):
    try:
        # Busca a simulação pelo ID fornecido
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id)
        data_atual_simulacao = simulacao.mes_atual.date() if isinstance(simulacao.mes_atual, datetime) else simulacao.mes_atual

        # Busca o histórico do ativo usando o yfinance com preços não ajustados
        ativo = yf.Ticker(ticker)
        historico = ativo.history(period='max', auto_adjust=False)

        if historico.empty:
            return {'exists': False, 'error': 'Sem histórico de preços para o ticker fornecido.'}, 404

        # Pega a primeira data disponível nos dados históricos
        data_inicio_ticker = historico.index[0].date()

        # Verifica se a data de início do ativo é anterior ou igual à data atual da simulação
        if data_inicio_ticker <= data_atual_simulacao:
            return {'exists': True, 'ticker': ticker, 'data_inicio': str(data_inicio_ticker)}, 200
        else:
            return {'exists': False, 'ticker': ticker, 'data_inicio': str(data_inicio_ticker)}, 200

    except Exception as e:
        return {'error': f'Ocorreu um erro: {str(e)}'}, 500
