from bcb import sgs
from datetime import datetime
import pandas as pd
import numpy as np
import time


def arredondar_para_baixo(valor):
    """
    Arredonda um valor para baixo, mantendo duas casas decimais.

    Args:
        valor (float): Valor a ser arredondado.

    Returns:
        float: Valor arredondado para baixo com duas casas decimais.
    """
    return np.floor(valor * 100) / 100


def pegar_inflacao(start_date, end_date, max_retries=5, retry_delay=2):
    """
    Obtém os dados de inflação (IPCA) entre duas datas específicas.

    Args:
        start_date (str): Data de início no formato 'YYYY-MM-DD'.
        end_date (str): Data de término no formato 'YYYY-MM-DD'.
        max_retries (int, optional): Número máximo de tentativas em caso de falha. Default é 5.
        retry_delay (int, optional): Intervalo de tempo (em segundos) entre tentativas. Default é 2.

    Returns:
        pd.DataFrame: DataFrame contendo as datas e valores do IPCA, ou None se falhar.
    """
    codigo_ipca = 433  # Código do IPCA no SGS
    attempt = 0  # Contador de tentativas

    while attempt < max_retries:
        try:
            # Pegando os dados diretamente como DataFrame
            df = sgs.get(codigo_ipca, start=start_date, end=end_date)

            # Verificar se a resposta está no formato esperado
            if df.empty:
                return None

            # Ajustar o DataFrame para ter duas colunas: Data e Valor
            df = df.reset_index()  # Reseta o índice para que a data vire uma coluna
            df.columns = ['Data', 'Valor']  # Renomeia as colunas

            return df  # Se tudo der certo, retorna o DataFrame

        except Exception as e:
            attempt += 1  # Incrementa o contador de tentativas
            time.sleep(retry_delay)  # Aguarda alguns segundos antes de tentar novamente

    return None


def ajustar_inflacao(ipca_data, coluna_ipca, periodo_inicial, valor, data_final):
    """
    Ajusta um valor considerando a inflação acumulada entre um período inicial e uma data final.

    Args:
        ipca_data (pd.DataFrame): DataFrame com dados do IPCA.
        coluna_ipca (str): Nome da coluna no DataFrame que contém os valores do IPCA.
        periodo_inicial (str or datetime.date): Data inicial do período de ajuste.
        valor (float): Valor a ser ajustado pela inflação.
        data_final (str or datetime.date): Data final do período de ajuste.

    Returns:
        float: Valor ajustado pela inflação, ou None em caso de erro.
    """
    try:
        # Converter periodo_inicial e data_final para objetos datetime se forem strings
        if isinstance(periodo_inicial, str):
            periodo_inicial = datetime.strptime(periodo_inicial, '%Y-%m-%d').date()
        if isinstance(data_final, str):
            data_final = datetime.strptime(data_final, '%Y-%m-%d').date()

        # Garantir que o índice do DataFrame seja do tipo datetime
        ipca_data.index = pd.to_datetime(ipca_data.index)

        # Filtrar os dados para o período relevante
        df_ipca = ipca_data.loc[data_final:periodo_inicial].copy()

        if df_ipca.empty:
            return None

        # Calcular o fator de correção acumulado
        df_ipca['IPCA'] = df_ipca[coluna_ipca] / 100
        df_ipca['Fator de Correcao'] = (1 + df_ipca['IPCA']).cumprod()

        # Calcular o valor equivalente
        fator_correcao_final = df_ipca['Fator de Correcao'].iloc[-1]
        valor_equivalente = valor / fator_correcao_final

        return valor_equivalente
    except KeyError as e:
        pass
    except IndexError as e:
        pass
    except Exception as e:
        pass
    return None


def ajustar_inflacao_automatica(ipca_data, coluna_ipca, periodo_inicial, valor, data_final):
    """
    Ajustar um valor considerando a inflação acumulada entre um período inicial e uma data final.

    Args:
        ipca_data (pd.DataFrame): DataFrame com dados de inflação.
        coluna_ipca (str): Nome da coluna da série temporal do IPCA no DataFrame.
        periodo_inicial (str or datetime.date): Data inicial no formato 'YYYY-MM-DD'.
        valor (float): Valor a ser ajustado.
        data_final (str or datetime.date): Data final no formato 'YYYY-MM-DD'.

    Returns:
        float: Valor ajustado pela inflação, ou None em caso de erro.
    """
    try:
        # Converter período_inicial e data_final para objetos datetime se forem strings
        if isinstance(periodo_inicial, str):
            periodo_inicial = datetime.strptime(periodo_inicial, '%Y-%m-%d').date()
        if isinstance(data_final, str):
            data_final = datetime.strptime(data_final, '%Y-%m-%d').date()

        # Garantir que o índice do DataFrame seja do tipo datetime
        ipca_data.index = pd.to_datetime(ipca_data.index)

        # Filtrar os dados para o período relevante
        df_ipca = ipca_data.loc[periodo_inicial:data_final].copy()

        # Calcular o fator de correção acumulado
        df_ipca['IPCA'] = df_ipca[coluna_ipca] / 100  # Converter porcentagem para fator decimal
        df_ipca['Fator de Correcao'] = (1 + df_ipca['IPCA']).cumprod()

        # Calcular o valor equivalente
        fator_correcao_final = df_ipca['Fator de Correcao'].iloc[-1]
        valor_equivalente = valor / fator_correcao_final

        return valor_equivalente
    except Exception as e:
        return None
