import yfinance as yf
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo

def negociar_ativo(simulacao_id, user, ticker):
    try:
        print(f"Iniciando negociação do ativo. Simulacao ID: {simulacao_id}, Usuário: {user}, Ticker: {ticker}")
        # Inicializa o objeto ativo no yfinance
        ativo = yf.Ticker(ticker)

        # Obtém a moeda do ativo (por exemplo, USD, BRL, etc.)
        moeda_ativo = ativo.info.get('currency', 'USD')
        print(f"Moeda do ativo obtida: {moeda_ativo}")

        # Obtém a simulação manual associada ao ID e ao usuário autenticado
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
        carteira_manual = simulacao.carteira_manual
        print(f"Simulação obtida: {simulacao.nome}, Carteira manual obtida.")

        # Obter 'mes_atual' da simulação
        mes_atual = simulacao.mes_atual
        print(f"Mês atual da simulação: {mes_atual}")

        # Tornar 'mes_atual' "aware" se for "naive"
        if timezone.is_naive(mes_atual):
            mes_atual = timezone.make_aware(mes_atual, timezone.get_default_timezone())
            print(f"Mês atual convertido para timezone aware: {mes_atual}")

        # Calcular a data de início (um ano antes de 'mes_atual')
        data_inicio = mes_atual - timedelta(days=365)
        print(f"Data de início calculada: {data_inicio}")

        # Verificar se o ativo está na carteira do usuário e obter a quantidade de posse
        ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()
        if ativo_na_carteira:
            print(f"Ativo encontrado na carteira: {ativo_na_carteira.nome}, Posse: {ativo_na_carteira.posse}")
        else:
            print("Ativo não encontrado na carteira.")

        if ativo_na_carteira and ativo_na_carteira.precos:
            # Usar os preços armazenados
            precos_armazenados = ativo_na_carteira.precos
            print(f"Preços armazenados encontrados para o ativo: {precos_armazenados}")

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
            print(f"Histórico de preços filtrado: {historico_lista}")

            # Obter o último preço de fechamento
            sorted_dates = sorted(precos_armazenados.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
            ultimo_preco = float(precos_armazenados[sorted_dates[-1]]['close'])
            print(f"Último preço de fechamento obtido dos preços armazenados: {ultimo_preco}")

        else:
            # Se não houver preços armazenados, faça a requisição externa ao yfinance
            print("Preços armazenados não encontrados. Obtendo preços do yfinance.")
            historico = ativo.history(
                start=data_inicio.strftime('%Y-%m-%d'),
                end=mes_atual.strftime('%Y-%m-%d'),
                auto_adjust=False,
                actions=True
            )
            print(f"Histórico de preços obtido do yfinance: {historico}")

            if historico.empty:
                print("Não há dados históricos para o período especificado.")
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
            print(f"Histórico de preços formatado: {historico_lista}")

            ultimo_preco = float(historico['Close'].iloc[-1])
            print(f"Último preço de fechamento obtido do yfinance: {ultimo_preco}")

        moeda_carteira = carteira_manual.moeda_base
        print(f"Moeda da carteira: {moeda_carteira}")

        # Se a moeda do ativo for diferente da moeda da carteira, faz a conversão
        if moeda_ativo != moeda_carteira:
            print(f"Moeda do ativo diferente da moeda da carteira. Realizando conversão de {moeda_ativo} para {moeda_carteira}")
            conversao_ticker = f"{moeda_ativo}{moeda_carteira}=X"
            historico_conversao = yf.Ticker(conversao_ticker).history(
                start=data_inicio.strftime('%Y-%m-%d'),
                end=mes_atual.strftime('%Y-%m-%d'),
                auto_adjust=False,
                actions=False
            )
            print(f"Histórico de conversão obtido: {historico_conversao}")

            taxa_conversao = float(historico_conversao['Close'].iloc[-1]) if not historico_conversao.empty else 1
            ultimo_preco_convertido = ultimo_preco * taxa_conversao
            ultimo_preco_convertido = arredondar_para_baixo(ultimo_preco_convertido)
            print(f"Último preço convertido: {ultimo_preco_convertido}")
        else:
            ultimo_preco_convertido = arredondar_para_baixo(ultimo_preco)
            print(f"Moeda do ativo e da carteira são iguais. Preço convertido: {ultimo_preco_convertido}")

        # Calcula a posse do ativo
        quantidade_ativo = ativo_na_carteira.posse if ativo_na_carteira else 0
        print(f"Quantidade de ativo na carteira: {quantidade_ativo}")
        valor_posse = quantidade_ativo * ultimo_preco_convertido if quantidade_ativo > 0 else 0
        valor_posse = arredondar_para_baixo(valor_posse)
        print(f"Valor da posse do ativo: {valor_posse}")

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
        print(f"Dados de resposta: {response_data}")

        return response_data, 200

    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
        return {'error': f'Ocorreu um erro: {str(e)}'}, 500
