from bcb import sgs
from datetime import datetime
import pandas as pd
import numpy as np
import time


def arredondar_para_baixo(valor):
    return np.floor(valor * 100) / 100


def pegar_inflacao(start_date, end_date, max_retries=5, retry_delay=2):
    codigo_ipca = 433  # Código do IPCA no SGS
    attempt = 0  # Contador de tentativas

    while attempt < max_retries:
        try:
            # Pegando os dados diretamente como DataFrame
            df = sgs.get(codigo_ipca, start=start_date, end=end_date)

            # Verificar se a resposta está no formato esperado
            if df.empty:
                print("Erro: DataFrame está vazio")
                return None

            # Ajustar o DataFrame para ter duas colunas: Data e Valor
            df = df.reset_index()  # Reseta o índice para que a data vire uma coluna
            df.columns = ['Data', 'Valor']  # Renomeia as colunas

            return df  # Se tudo der certo, retorna o DataFrame

        except Exception as e:
            print(f"Tentativa {attempt + 1}/{max_retries} falhou: {e}")
            attempt += 1  # Incrementa o contador de tentativas
            time.sleep(retry_delay)  # Aguarda alguns segundos antes de tentar novamente

    print("Erro: todas as tentativas de pegar os dados de inflação falharam.")
    return None


"""# Exemplo de uso
inflacao = pegar_inflacao('2020-01-01', '2024-08-16')
print(inflacao['Data'])
"""


def ajustar_inflacao(ipca_data, coluna_ipca, periodo_inicial, valor, data_final):
    try:
        # Convert periodo_inicial and data_final to datetime objects if they're strings
        if isinstance(periodo_inicial, str):
            periodo_inicial = datetime.strptime(periodo_inicial, '%Y-%m-%d').date()
        if isinstance(data_final, str):
            data_final = datetime.strptime(data_final, '%Y-%m-%d').date()

        # Ensure the DataFrame index is datetime type
        ipca_data.index = pd.to_datetime(ipca_data.index)

        print(f"IPCA data range: {ipca_data.index.min()} to {ipca_data.index.max()}")
        print(f"Requested range: {periodo_inicial} to {data_final}")

        # Filter data for the relevant period
        df_ipca = ipca_data.loc[data_final:periodo_inicial].copy()

        if df_ipca.empty:
            print("No data found in the specified date range.")
            return None

        print(f"Filtered IPCA data:\n{df_ipca}")

        # Calculate the cumulative correction factor
        df_ipca['IPCA'] = df_ipca[coluna_ipca] / 100
        df_ipca['Fator de Correcao'] = (1 + df_ipca['IPCA']).cumprod()

        # Calculate the equivalent value
        fator_correcao_final = df_ipca['Fator de Correcao'].iloc[-1]
        valor_equivalente = valor / fator_correcao_final

        print(f"Final correction factor: {fator_correcao_final}")
        print(f"Equivalent value: {valor_equivalente}")

        return valor_equivalente
    except KeyError as e:
        print(f"KeyError: {e}. Available columns: {ipca_data.columns}")
    except IndexError as e:
        print(f"IndexError: {e}. This might be due to an empty DataFrame after filtering.")
    except Exception as e:
        print(f"Error adjusting inflation: {e}")
    return None


# A simulação automática quebrou com a nova alteração na função de ajuste de inflação, optei pela via mais rápida
def ajustar_inflacao_automatica(ipca_data, coluna_ipca, periodo_inicial, valor, data_final):
    """
    Ajustar um valor considerando a inflação acumulada entre um período inicial e uma data final.

    :param ipca_data: DataFrame com dados de inflação
    :param coluna_ipca: Nome da coluna da série temporal do IPCA no DataFrame
    :param periodo_inicial: Data inicial no formato 'YYYY-MM-DD'
    :param valor: Valor a ser ajustado
    :param data_final: Data final no formato 'YYYY-MM-DD'
    :return: Valor ajustado pela inflação
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
        print(f"Erro ao ajustar inflação: {e}")
        return None
