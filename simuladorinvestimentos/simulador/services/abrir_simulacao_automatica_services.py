import pandas as pd

from ..models import SimulacaoAutomatica


def processar_simulacao_automatica(simulacao_id):
    """
    Processa os dados de uma simulação automática e retorna informações sobre a simulação e o resultado.

    Args:
        simulacao_id (int): ID da simulação automática a ser processada.

    Returns:
        tuple: Dicionário contendo detalhes da simulação e o resultado, juntamente com o código de status HTTP.
    """
    try:
        # Buscar a simulação automática pelo ID fornecido
        try:
            simulacao = SimulacaoAutomatica.objects.get(id=simulacao_id)
        except SimulacaoAutomatica.DoesNotExist:
            return {'error': 'Simulação não encontrada.'}, 404

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

        # Processar o DataFrame de resultados
        df_resultado = pd.DataFrame(simulacao.resultados)  # Ajustar logicamente conforme necessário

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
            'resultado': df_resultado.to_dict(orient='records')  # Convertendo o DataFrame para formato JSON
        }

        return resposta, 200

    except Exception as e:
        return {'error': f'Erro inesperado: {str(e)}'}, 500
