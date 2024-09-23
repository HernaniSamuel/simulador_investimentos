import json
import yfinance as yf
from ..models import CarteiraAutomatica, SimulacaoAutomatica, Ativo


def enviar_ativos_para_carteira(data):
    carteira_id = data.get('carteira_id')
    simulacao_id = data.get('simulacao_id')

    if not carteira_id or not simulacao_id:
        return {'error': 'Missing carteira_id or simulacao_id'}, 400

    try:
        carteira_automatica = CarteiraAutomatica.objects.get(id=carteira_id)
    except CarteiraAutomatica.DoesNotExist:
        return {'error': 'CarteiraAutomatica not found'}, 404

    try:
        simulacao_automatica = SimulacaoAutomatica.objects.get(id=simulacao_id)
    except SimulacaoAutomatica.DoesNotExist:
        return {'error': 'SimulacaoAutomatica not found'}, 404

    moeda_carteira = carteira_automatica.moeda_base

    # Dicionário para armazenar as taxas de câmbio baixadas
    cambio_cache = {}

    for item in data['ativos']:
        ticker = item['ticker']
        peso = item['peso']
        print(f"Processando ativo: {ticker} com peso {peso}")

        # Obtendo informações do ativo
        ativo_info = yf.Ticker(ticker).info
        nome = ativo_info['longName']
        moeda_ativo = ativo_info['currency']

        # Pegar preços dos ativos
        precos_df = yf.download(ticker, start=simulacao_automatica.data_inicial,
                                end=simulacao_automatica.data_final, interval='1mo')

        # Pegar a data de início de negociação do ativo
        data_lancamento = precos_df.index.min().date() if not precos_df.empty else None

        # Se a moeda do ativo for diferente da moeda da carteira, faça a conversão
        if moeda_ativo != moeda_carteira:
            print(f"Convertendo preços de {moeda_ativo} para {moeda_carteira}")

            # Verificar se o câmbio já está no cache
            if moeda_ativo in cambio_cache:
                cambio_df = cambio_cache[moeda_ativo]
            else:
                cambio_ticker = f"{moeda_ativo}{moeda_carteira}=X"
                cambio_df = yf.download(cambio_ticker, start=simulacao_automatica.data_inicial,
                                        end=simulacao_automatica.data_final, interval='1mo')
                cambio_cache[moeda_ativo] = cambio_df  # Armazenar no cache

            # Garantindo que a data do câmbio corresponde à data dos preços do ativo
            cambio_df = cambio_df.reindex(precos_df.index, method='ffill')

            # Convertendo preços para a moeda da carteira
            precos_df['Adj Close'] = precos_df['Adj Close'] * cambio_df['Adj Close']

        # Converter DataFrame para lista de dicionários com datas como strings
        precos = precos_df.reset_index().to_dict(orient='records')
        for preco in precos:
            preco['Date'] = preco['Date'].isoformat()  # Converter Timestamp para string ISO 8601

        print(f"Criando objeto Ativo para {ticker}")
        ativo = Ativo.objects.create(
            ticker=ticker,
            peso=peso,
            posse=0,
            nome=nome,
            precos=json.dumps(precos),
            data_lancamento=data_lancamento  # Salvando a data de lançamento do ativo
        )
        carteira_automatica.ativos.add(ativo)

    return {'status': 'success'}, 200
