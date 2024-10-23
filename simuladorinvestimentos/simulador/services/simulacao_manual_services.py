from django.shortcuts import get_object_or_404
from datetime import datetime
import json
from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo


def calcular_simulacao_manual(simulacao_id):
    simulacao_manual = get_object_or_404(SimulacaoManual, id=simulacao_id)
    ativos = simulacao_manual.carteira_manual.ativos.filter(posse__gt=0)

    resultado_mes = []  # Lista para armazenar o valor de cada ativo no mês atual
    pie_data = []

    # Carregar o historico_valor_total
    if simulacao_manual.historico_valor_total:
        line_data_valor_total = json.loads(simulacao_manual.historico_valor_total)
    else:
        line_data_valor_total = []

    line_data = {
        'valorTotal': line_data_valor_total,
        'valorAtivos': [],
    }

    mes_atual = simulacao_manual.mes_atual.strftime('%Y-%m-%d')

    # Loop pelos ativos para calcular os valores
    for ativo in ativos:
        posse = ativo.posse or 0

        # Obter o último preço convertido ou o último preço de 'precos'
        if ativo.ultimo_preco_convertido is not None:
            ultimo_preco = ativo.ultimo_preco_convertido
        else:
            # Verificar se 'precos' não está vazio
            if ativo.precos:
                precos_dict = ativo.precos
                try:
                    # Converter as chaves (datas) em objetos datetime
                    date_prices = [
                        (datetime.strptime(date_str, '%Y-%m-%d'), price)
                        for date_str, price in precos_dict.items()
                    ]
                    # Ordenar por data e obter o preço mais recente até o mes_atual
                    date_prices = [dp for dp in date_prices if dp[0] <= simulacao_manual.mes_atual]
                    if date_prices:
                        date_prices.sort()
                        ultimo_preco = date_prices[-1][1]
                    else:
                        ultimo_preco = 0
                except Exception as e:
                    # Em caso de erro na conversão, definir preço como 0
                    ultimo_preco = 0
            else:
                ultimo_preco = 0

        valor_ativo = posse * ultimo_preco
        valor_ativo = arredondar_para_baixo(valor_ativo)
        resultado_mes.append(valor_ativo)
        line_data['valorAtivos'].append(posse)

    # Calcular o total do mês
    total_mes = sum(resultado_mes)

    # Atualizar o último valor em 'valorTotal' ou adicionar se estiver vazio
    if line_data['valorTotal']:
        line_data['valorTotal'][-1] = total_mes
    else:
        line_data['valorTotal'].append(total_mes)

    # Atualizar o historico_valor_total sem avançar o mês
    simulacao_manual.historico_valor_total = json.dumps(line_data['valorTotal'])
    simulacao_manual.save()

    # Calcular os dados do gráfico de pizza
    for ativo, valor_ativo in zip(ativos, resultado_mes):
        peso_ativo = valor_ativo / total_mes if total_mes > 0 else 0
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
