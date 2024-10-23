from django.shortcuts import get_object_or_404
from ..models import SimulacaoManual


def calcular_simulacao_manual(simulacao_id):
    simulacao_manual = get_object_or_404(SimulacaoManual, id=simulacao_id)
    ativos = simulacao_manual.carteira_manual.ativos.filter(posse__gt=0)

    valor_total_ativos = 0
    soma_ponderada_posses_precos = 0
    pie_data = []
    line_data = {
        'valorTotal': simulacao_manual.historico_valor_total or [],
        'valorAtivos': [],
    }
    mes_atual = simulacao_manual.mes_atual.strftime('%Y-%m-%d')

    # Loop pelos ativos para calcular os valores
    for ativo in ativos:
        precos_armazenados = ativo.precos
        if precos_armazenados:
            ultimo_preco_data = list(precos_armazenados.values())[-1]
            ultimo_preco = ultimo_preco_data.get('close', 0)
        else:
            ultimo_preco = 0
        valor_ativo = ativo.posse * ultimo_preco
        valor_total_ativos += valor_ativo
        soma_ponderada_posses_precos += valor_ativo
        line_data['valorAtivos'].append(ativo.posse)

    # Calcula os dados do gráfico de pizza (pie chart)
    for ativo in ativos:
        precos_armazenados = ativo.precos
        if precos_armazenados:
            ultimo_preco_data = list(precos_armazenados.values())[-1]
            ultimo_preco = ultimo_preco_data.get('close', 0)
        else:
            ultimo_preco = 0
        peso_ativo = (
                                 ativo.posse * ultimo_preco) / soma_ponderada_posses_precos if soma_ponderada_posses_precos > 0 else 0
        pie_data.append({
            'name': ativo.nome,
            'y': round(peso_ativo * 100, 2)
        })

    cash = simulacao_manual.carteira_manual.valor_em_dinheiro

    # Dados finais para resposta
    response_data = {
        'nome_simulacao': simulacao_manual.nome,
        'lineData': line_data,
        'pieData': pie_data,
        'cash': cash,
        'mes_atual': mes_atual,
    }

    return response_data
