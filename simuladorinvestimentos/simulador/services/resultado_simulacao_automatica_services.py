import json

import pandas as pd
from datetime import datetime

from ..models import SimulacaoAutomatica
from ..utils import ajustar_inflacao_automatica, arredondar_para_baixo


def safe_strptime(date_str, format='%Y-%m-%d'):
    """
    Faz a conversão segura de uma string para um objeto datetime.date.

    Args:
        date_str (str): Data no formato de string.
        format (str): Formato da data. Default é '%Y-%m-%d'.

    Returns:
        datetime.date ou None: Retorna o objeto datetime.date, ou None se falhar.
    """
    try:
        return datetime.strptime(date_str, format).date()
    except ValueError:
        return None


def get_ipca_data(simulacao):
    """
    Obtém os dados de IPCA de uma simulação.

    Args:
        simulacao (SimulacaoAutomatica): Objeto da simulação automática.

    Returns:
        pd.DataFrame: DataFrame contendo os dados do IPCA.
    """
    ipca_data = pd.DataFrame(simulacao.inflacao_total)
    ipca_data['Data'] = pd.to_datetime(ipca_data['Data'], format='%Y-%m-%d')
    ipca_data.set_index('Data', inplace=True)
    return ipca_data


def adjust_initial_application(simulacao, ipca_data, data_inicial, data_final):
    """
    Ajusta a aplicação inicial de acordo com a inflação acumulada.

    Args:
        simulacao (SimulacaoAutomatica): Objeto da simulação automática.
        ipca_data (pd.DataFrame): DataFrame com os dados do IPCA.
        data_inicial (datetime): Data inicial.
        data_final (datetime): Data final.

    Returns:
        float: Valor ajustado da aplicação inicial.
    """
    return ajustar_inflacao_automatica(
        periodo_inicial=data_inicial,
        ipca_data=ipca_data,
        coluna_ipca='Valor',
        valor=simulacao.aplicacao_inicial,
        data_final=data_final
    ) or 0


def adjust_monthly_applications(simulacao, ipca_data, data_inicial, data_final):
    """
    Ajusta as aplicações mensais com base na inflação.

    Args:
        simulacao (SimulacaoAutomatica): Objeto da simulação automática.
        ipca_data (pd.DataFrame): DataFrame com os dados do IPCA.
        data_inicial (datetime): Data inicial.
        data_final (datetime): Data final.

    Returns:
        tuple: Lista das aplicações mensais ajustadas e datas válidas.
    """
    aplicacoes_mensais_ajustadas = []
    datas_validas = ipca_data.loc[
        (ipca_data.index >= data_inicial) & (ipca_data.index <= data_final)].index

    for data_corrente in datas_validas:
        aplicacao_mensal_ajustada = ajustar_inflacao_automatica(
            periodo_inicial=data_corrente,
            ipca_data=ipca_data,
            coluna_ipca='Valor',
            valor=simulacao.aplicacao_mensal,
            data_final=data_final
        ) or 0
        aplicacao_mensal_ajustada = arredondar_para_baixo(aplicacao_mensal_ajustada)
        aplicacoes_mensais_ajustadas.append(aplicacao_mensal_ajustada)
    return aplicacoes_mensais_ajustadas, datas_validas


def calculate_meses_desde_lancamento(data_corrente, data_lancamento):
    """
    Calcula o número de meses desde o lançamento do ativo até a data corrente.

    Args:
        data_corrente (datetime): Data corrente.
        data_lancamento (datetime): Data de lançamento do ativo.

    Returns:
        int: Número de meses desde o lançamento.
    """
    return (data_corrente.year - data_lancamento.year) * 12 + (data_corrente.month - data_lancamento.month)


def get_preco_ativo(ativo, meses_desde_lancamento):
    """
    Obtém o preço do ativo para um determinado mês desde seu lançamento.

    Args:
        ativo (object): Objeto do ativo.
        meses_desde_lancamento (int): Meses desde o lançamento do ativo.

    Returns:
        float ou None: Preço do ativo, ou None se não estiver disponível.
    """
    precos = ativo.precos_json
    if meses_desde_lancamento < len(precos):
        valor_adj_close = precos[meses_desde_lancamento].get('Adj Close', 0)

        # Verificar se o valor é NaN usando pd.isna()
        if pd.isna(valor_adj_close):
            valor_adj_close = 0  # Substituir NaN por 0

        return valor_adj_close
    else:
        return None


def update_ativos_for_date(ativos, data_corrente, valor_inicial_mes, valor_total_carteira):
    """
    Atualiza a quantidade de ativos para uma data específica.

    Args:
        ativos (list): Lista de ativos.
        data_corrente (datetime): Data corrente.
        valor_inicial_mes (float): Valor inicial do mês.
        valor_total_carteira (float): Valor total da carteira.

    Returns:
        float: Valor total da carteira atualizado.
    """
    for ativo in ativos:
        if ativo.data_lancamento_ts and data_corrente >= ativo.data_lancamento_ts:
            meses_desde_lancamento = calculate_meses_desde_lancamento(data_corrente, ativo.data_lancamento_ts)
            preco_ativo = get_preco_ativo(ativo, meses_desde_lancamento)

            if preco_ativo is not None and preco_ativo > 0:
                valor_investido = valor_inicial_mes * ativo.peso
                quantidade_comprada = valor_investido / preco_ativo
                ativo.posse += quantidade_comprada
                valor_total_carteira -= valor_investido

    return valor_total_carteira


def calculate_valor_total_ativos_mes(ativos, data_corrente):
    """
    Calcula o valor total dos ativos para um determinado mês.

    Args:
        ativos (list): Lista de ativos.
        data_corrente (datetime): Data corrente.

    Returns:
        float: Valor total dos ativos.
    """
    total = 0

    for ativo in ativos:
        if ativo.data_lancamento_ts and data_corrente >= ativo.data_lancamento_ts:
            meses_desde_lancamento = calculate_meses_desde_lancamento(data_corrente, ativo.data_lancamento_ts)
            preco_ativo = get_preco_ativo(ativo, meses_desde_lancamento)
            if preco_ativo is not None:
                total += arredondar_para_baixo(ativo.posse * preco_ativo)

    return total


def simulate_monthly_investments(ativos, aplicacoes_mensais_ajustadas, datas_validas, aplicacao_inicial_ajustada):
    """
    Simula os investimentos mensais.

    Args:
        ativos (list): Lista de ativos.
        aplicacoes_mensais_ajustadas (list): Lista de aplicações mensais ajustadas.
        datas_validas (list): Datas válidas para a simulação.
        aplicacao_inicial_ajustada (float): Aplicação inicial ajustada.

    Returns:
        list: Lista contendo o valor total da carteira em cada mês.
    """
    adjclose_carteira = []
    valor_total_carteira = aplicacao_inicial_ajustada

    for mes_index, data_corrente in enumerate(datas_validas):
        # Adiciona a aplicação mensal ajustada
        valor_total_carteira += aplicacoes_mensais_ajustadas[mes_index]
        valor_inicial_mes = valor_total_carteira

        # Atualiza os ativos
        valor_total_carteira = update_ativos_for_date(
            ativos, data_corrente, valor_inicial_mes, valor_total_carteira
        )
        valor_total_carteira = arredondar_para_baixo(valor_total_carteira)

        # Calcula o valor total dos ativos no mês
        valor_total_ativos_mes = calculate_valor_total_ativos_mes(ativos, data_corrente)

        # Calcula o valor total da carteira no mês
        valor_total_carteira_mes = valor_total_ativos_mes + valor_total_carteira

        # Adiciona ao histórico
        adjclose_carteira.append((data_corrente, valor_total_carteira_mes))

    return adjclose_carteira


def save_simulation_results(simulacao, adjclose_carteira):
    """
    Salva os resultados da simulação.

    Args:
        simulacao (SimulacaoAutomatica): Objeto da simulação automática.
        adjclose_carteira (list): Lista contendo o valor total da carteira em cada mês.

    Returns:
        pd.DataFrame: DataFrame com os resultados da simulação.
    """
    # Cria DataFrame com datas e valores
    df_resultado = pd.DataFrame(adjclose_carteira, columns=['Data', 'Valor'])

    # Converte datas para strings antes de salvar
    df_resultado['Data'] = df_resultado['Data'].dt.strftime('%Y-%m-%d')

    # Converte para formato JSON
    simulacao.resultados = df_resultado.to_dict(orient='records')

    # Salva a simulação com os resultados atualizados
    simulacao.save()

    return df_resultado


def collect_ativos_info(ativos):
    """
    Coleta informações dos ativos.

    Args:
        ativos (list): Lista de ativos.

    Returns:
        list: Lista contendo informações dos ativos.
    """
    ativos_info = [
        {
            'nome': ativo.nome,
            'ticker': ativo.ticker,
            'peso': ativo.peso,
            'posse': ativo.posse
        }
        for ativo in ativos
    ]
    return ativos_info


def calcular_resultado_simulacao(simulacao_id):
    """
    Calcula o resultado de uma simulação automática com base nos parâmetros fornecidos.

    Args:
        simulacao_id (int): ID da simulação a ser calculada.

    Returns:
        tuple: Dicionário contendo o resultado da simulação e código de status HTTP.
    """
    try:
        simulacao = SimulacaoAutomatica.objects.get(id=simulacao_id)

        ipca_data = get_ipca_data(simulacao)

        data_inicial = pd.to_datetime(simulacao.data_inicial)
        data_final = pd.to_datetime(simulacao.data_final)

        if data_inicial is None or data_final is None:
            return {'error': 'Formato de data inválido'}, 400

        aplicacao_inicial_ajustada = adjust_initial_application(simulacao, ipca_data, data_inicial, data_final)
        aplicacao_inicial_ajustada = arredondar_para_baixo(aplicacao_inicial_ajustada)

        aplicacoes_mensais_ajustadas, datas_validas = adjust_monthly_applications(simulacao, ipca_data, data_inicial, data_final)

        ativos = list(simulacao.carteira_automatica.ativos.all())
        for ativo in ativos:
            ativo.precos_json = json.loads(ativo.precos)
            ativo.data_lancamento_ts = pd.Timestamp(ativo.data_lancamento) if ativo.data_lancamento else None

        adjclose_carteira = simulate_monthly_investments(ativos, aplicacoes_mensais_ajustadas, datas_validas, aplicacao_inicial_ajustada)

        df_resultado = save_simulation_results(simulacao, adjclose_carteira)

        ativos_info = collect_ativos_info(ativos)

        for ativo in ativos:
            ativo.save()

        resposta = {
            'simulacao': {
                'valor_inicial': simulacao.aplicacao_inicial,
                'valor_mensal': simulacao.aplicacao_mensal,
                'data_inicial': simulacao.data_inicial,
                'data_final': simulacao.data_final,
                'ativos': ativos_info
            },
            'resultado': df_resultado.to_dict(orient='records')
        }

        return resposta, 200

    except SimulacaoAutomatica.DoesNotExist:
        return {'error': 'SimulacaoAutomatica não encontrada'}, 404
    except Exception as e:
        print(f'Erro durante a simulação: {str(e)}')
        return {'error': str(e)}, 500
