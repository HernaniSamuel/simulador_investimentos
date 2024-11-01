import yfinance as yf

from django.utils import timezone
from django.shortcuts import get_object_or_404

from datetime import datetime, timedelta

from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo


def negociar_ativo(simulacao_id, user, ticker):
    """
    Realiza a negociação de um ativo especificado em uma simulação manual.

    Args:
        simulacao_id (int): ID da simulação manual.
        user (User): Usuário autenticado realizando a operação.
        ticker (str): Ticker do ativo a ser negociado.

    Returns:
        tuple: Dados da resposta e status HTTP (200 em caso de sucesso, 404 ou 500 em caso de falha).
    """
    try:
        # Inicializa o objeto ativo no yfinance
        ativo = yf.Ticker(ticker)

        # Obtém a moeda do ativo (por exemplo, USD, BRL, etc.)
        moeda_ativo = ativo.info.get('currency', 'USD')

        # Obtém a simulação manual associada ao ID e ao usuário autenticado
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
        carteira_manual = simulacao.carteira_manual

        # Obter 'mes_atual' da simulação e torná-lo "aware" se for "naive"
        mes_atual = simulacao.mes_atual
        if timezone.is_naive(mes_atual):
            mes_atual = timezone.make_aware(mes_atual, timezone.get_default_timezone())

        # Calcular a data de início (um ano antes de 'mes_atual')
        data_inicio = mes_atual - timedelta(days=365)

        # Verificar se o ativo está na carteira do usuário e obter a quantidade de posse
        ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()

        if ativo_na_carteira and ativo_na_carteira.precos:
            # Usar os preços armazenados
            precos_armazenados = ativo_na_carteira.precos

            # Filtrar os preços dentro do intervalo de datas
            historico_lista = [
                {
                    'date': data,
                    'open': preco['open'],
                    'high': preco['high'],
                    'low': preco['low'],
                    'close': preco['close']
                }
                for data, preco in precos_armazenados.items()
                if data_inicio.date() <= datetime.strptime(data, '%Y-%m-%d').date() <= mes_atual.date()
            ]

            # Obter o último preço de fechamento
            sorted_dates = sorted(precos_armazenados.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
            ultimo_preco = float(precos_armazenados[sorted_dates[-1]]['close'])

        else:
            # Se não houver preços armazenados, faça a requisição externa ao yfinance
            historico = ativo.history(
                start=data_inicio.strftime('%Y-%m-%d'),
                end=mes_atual.strftime('%Y-%m-%d'),
                auto_adjust=False,
                actions=True
            )

            if historico.empty:
                return {'error': 'Não há dados históricos para o período especificado.'}, 404

            historico_lista = [
                {
                    'date': str(index.date()),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close']
                }
                for index, row in historico.iterrows()
            ]

            ultimo_preco = float(historico['Close'].iloc[-1])

        # Obter a moeda da carteira
        moeda_carteira = carteira_manual.moeda_base

        # Se a moeda do ativo for diferente da moeda da carteira, faz a conversão
        if moeda_ativo != moeda_carteira:
            conversao_ticker = f"{moeda_ativo}{moeda_carteira}=X"
            historico_conversao = yf.Ticker(conversao_ticker).history(
                start=data_inicio.strftime('%Y-%m-%d'),
                end=mes_atual.strftime('%Y-%m-%d'),
                auto_adjust=False,
                actions=False
            )

            taxa_conversao = float(historico_conversao['Close'].iloc[-1]) if not historico_conversao.empty else 1
            ultimo_preco_convertido = arredondar_para_baixo(ultimo_preco * taxa_conversao)
        else:
            ultimo_preco_convertido = arredondar_para_baixo(ultimo_preco)

        # Calcula a posse do ativo
        quantidade_ativo = ativo_na_carteira.posse if ativo_na_carteira else 0
        valor_posse = arredondar_para_baixo(quantidade_ativo * ultimo_preco_convertido) if quantidade_ativo > 0 else 0

        # Monta os dados da resposta
        response_data = {
            'ticker': ticker,
            'historico': historico_lista,
            'dinheiro_em_caixa': carteira_manual.valor_em_dinheiro,
            'preco_convertido': ultimo_preco_convertido,
            'moeda_ativo': moeda_ativo,
            'moeda_carteira': moeda_carteira,
            'quantidade_ativo': quantidade_ativo,
            'valor_posse': valor_posse,
            'ultimo_preco': ultimo_preco,
            'nome_simulacao': simulacao.nome
        }

        return response_data, 200

    except Exception as e:
        return {'error': f'Ocorreu um erro: {str(e)}'}, 500
