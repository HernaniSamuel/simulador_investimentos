from ..models import Historico


def obter_historico_usuario(usuario):
    """
    Obtém o histórico de simulações de um usuário específico.

    Args:
        usuario (User): Usuário cujo histórico será obtido.

    Returns:
        list: Lista de dicionários contendo informações das simulações automáticas e manuais do usuário.
    """
    historico = Historico.objects.filter(usuario=usuario)

    historico_list = [
        {
            'id': item.id,
            'simulacoes_automaticas': [
                {
                    'simulacao_id': simulacao.id,
                    'nome': simulacao.nome,
                    'data_criacao': item.data_criacao,
                    'data_inicial': simulacao.data_inicial,
                    'data_final': simulacao.data_final,
                    'aplicacao_inicial': simulacao.aplicacao_inicial,
                    'aplicacao_mensal': simulacao.aplicacao_mensal,
                }
                for simulacao in item.simulacoes_automaticas.all()
            ],
            'simulacoes_manuais': [
                {
                    'simulacao_id': simulacao.id,
                    'nome': simulacao.nome,
                    'data_criacao': item.data_criacao,
                    'data_inicial': simulacao.data_inicial,
                    'valor_total_carteira': (
                        simulacao.carteira_manual.valor_em_dinheiro + simulacao.carteira_manual.valor_ativos
                        if simulacao.carteira_manual.valor_em_dinheiro is not None and simulacao.carteira_manual.valor_ativos is not None
                        else 0
                    ),
                }
                for simulacao in item.simulacoes_manuais.all()
            ]
        }
        for item in historico
    ]

    return historico_list
