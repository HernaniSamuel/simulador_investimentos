from django.shortcuts import get_object_or_404
from datetime import datetime
import json
from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo


def calcular_simulacao_manual(simulacao_id):
    """
    Calcula o valor de uma simulação manual de investimentos com base no histórico de preços dos ativos.

    Args:
        simulacao_id (int): ID da simulação manual a ser calculada.

    Returns:
        dict: Dados finais da simulação, incluindo dados de linha e de pizza, além do valor total em dinheiro.
    """
    # Obtém o objeto SimulacaoManual usando o ID fornecido ou retorna um erro 404 se não for encontrado
    simulacao_manual = get_object_or_404(SimulacaoManual, id=simulacao_id)
    # Filtra os ativos da carteira manual que possuem uma quantidade de posse maior que zero
    ativos = simulacao_manual.carteira_manual.ativos.filter(posse__gt=0)

    resultado_mes = []  # Lista para armazenar o valor de cada ativo no mês atual
    pie_data = []  # Lista para armazenar os dados do gráfico de pizza

    # Carrega o histórico de valor total, se disponível, ou inicializa como uma lista vazia
    line_data_valor_total = json.loads(simulacao_manual.historico_valor_total) if simulacao_manual.historico_valor_total else []

    line_data = {
        'valorTotal': line_data_valor_total,  # Histórico dos valores totais
        'valorAtivos': [],  # Lista para armazenar a quantidade de cada ativo
    }

    # Converte a data do mês atual para o formato de string
    mes_atual = simulacao_manual.mes_atual.strftime('%Y-%m-%d')

    # Loop pelos ativos para calcular os valores
    for ativo in ativos:
        posse = ativo.posse or 0  # Quantidade de posse do ativo, ou 0 se não definida

        # Obter o último preço convertido ou o último preço de 'precos'
        if ativo.ultimo_preco_convertido is not None:
            # Utiliza o último preço convertido, se disponível
            ultimo_preco = ativo.ultimo_preco_convertido
        else:
            # Verifica se há preços disponíveis no histórico do ativo
            if ativo.precos:
                precos_dict = ativo.precos
                try:
                    # Converte as chaves (datas) em objetos datetime para facilitar a manipulação
                    date_prices = [
                        (datetime.strptime(date_str, '%Y-%m-%d'), price)
                        for date_str, price in precos_dict.items()
                    ]
                    # Filtra os preços que são anteriores ou iguais ao mês atual
                    date_prices = [dp for dp in date_prices if dp[0] <= simulacao_manual.mes_atual]
                    if date_prices:
                        # Ordena os preços por data e seleciona o mais recente
                        date_prices.sort()
                        ultimo_preco = date_prices[-1][1]
                    else:
                        # Define o preço como 0 se não houver preços válidos
                        ultimo_preco = 0
                except Exception as e:
                    # Em caso de erro na conversão dos preços, define o preço como 0
                    ultimo_preco = 0
            else:
                # Define o preço como 0 se não houver histórico de preços
                ultimo_preco = 0

        # Calcula o valor do ativo baseado na quantidade de posse e no último preço
        valor_ativo = posse * ultimo_preco
        valor_ativo = arredondar_para_baixo(valor_ativo)  # Arredonda o valor do ativo para baixo
        resultado_mes.append(valor_ativo)  # Adiciona o valor do ativo ao resultado do mês
        line_data['valorAtivos'].append(posse)  # Adiciona a quantidade de posse ao line_data

    # Calcula o valor total do mês somando o valor de todos os ativos
    total_mes = sum(resultado_mes)

    # Atualiza o último valor em 'valorTotal' ou adiciona se estiver vazio
    if line_data['valorTotal']:
        line_data['valorTotal'][-1] = total_mes  # Atualiza o último valor do histórico
    else:
        line_data['valorTotal'].append(total_mes)  # Adiciona o valor total como o primeiro valor do histórico

    # Atualiza o histórico de valor total da simulação manual e salva
    simulacao_manual.historico_valor_total = json.dumps(line_data['valorTotal'])
    simulacao_manual.save()

    # Loop para calcular os dados do gráfico de pizza, que representam a participação de cada ativo
    for ativo, valor_ativo in zip(ativos, resultado_mes):
        peso_ativo = valor_ativo / total_mes if total_mes > 0 else 0  # Calcula o peso do ativo em relação ao total
        pie_data.append({
            'name': ativo.nome,  # Nome do ativo
            'y': round(peso_ativo * 100, 2)  # Percentual do valor do ativo em relação ao total
        })

    # Obtém o valor em dinheiro disponível na carteira manual
    cash = simulacao_manual.carteira_manual.valor_em_dinheiro

    # Dados finais para resposta, incluindo o nome da simulação, dados de linha, dados de pizza e valor em dinheiro
    response_data = {
        'nome_simulacao': simulacao_manual.nome,
        'lineData': line_data,
        'pieData': pie_data,
        'cash': cash,
        'mes_atual': mes_atual,
    }

    return response_data
