from bcb import sgs
from datetime import datetime
import pandas as pd
import numpy as np


def arredondar_para_baixo(valor):
    return np.floor(valor * 100) / 100


def pegar_inflacao(start_date, end_date):
    codigo_ipca = 433  # Código do IPCA no SGS
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

        return df

    except Exception as e:
        print(f"Erro ao pegar inflação: {e}")
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