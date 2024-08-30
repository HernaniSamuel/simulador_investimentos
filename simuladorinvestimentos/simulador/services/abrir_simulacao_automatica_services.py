import pandas as pd
from ..models import SimulacaoAutomatica


def processar_simulacao_automatica(simulacao_id):
    try:
        simulacao = SimulacaoAutomatica.objects.get(id=simulacao_id)
    except SimulacaoAutomatica.DoesNotExist:
        return {'error': 'Simulacao not found'}, 404

    # Coletar informações dos ativos relacionados à simulação
    ativos = simulacao.carteira_automatica.ativos.all()
    ativos_info = [
        {
            'nome': ativo.nome,
            'ticker': ativo.ticker,
            'peso': ativo.peso,
            'posse': ativo.posse
        }
        for ativo in ativos
    ]

    # Simulação do dataframe 'df_resultado', substitua pela lógica adequada
    df_resultado = pd.DataFrame(simulacao.resultados)  # Ajuste conforme necessário

    # Estruturar a resposta JSON
    resposta = {
        'simulacao': {
            'valor_inicial': simulacao.aplicacao_inicial,
            'valor_mensal': simulacao.aplicacao_mensal,
            'data_inicial': simulacao.data_inicial,
            'data_final': simulacao.data_final,
            'nome': simulacao.nome,
            'ativos': ativos_info
        },
        'resultado': df_resultado.to_dict(orient='records')  # Convertendo o dataframe para um formato JSON
    }

    return resposta, 200
