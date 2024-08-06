from bcb import sgs
import pandas as pd
from datetime import datetime
import json


def pegar_inflacao(start_date):
    codigo_ipca = 433  # Código do IPCA no SGS
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')

        # Adicionando log para verificar as datas
        print(f"Tentando obter dados de {start_date} até {end_date}")

        # Pegando os dados
        df = sgs.get(codigo_ipca, start=start_date, end=end_date)

        # Verificando se o df é realmente um DataFrame
        if not isinstance(df, pd.DataFrame):
            print(f"Erro: Resposta não é um DataFrame. Tipo recebido: {type(df)}")
            print(f"Conteúdo da resposta: {df}")
            return None

        print(f"Resposta da API: {df}")

        if df.empty:
            print("Erro: DataFrame está vazio")
            return None

        # Verificando as colunas do DataFrame
        print(f"Colunas do DataFrame: {df.columns}")

        # Tentando somar os valores da primeira coluna
        try:
            inflacao_total = df.iloc[:, 0].sum()
            return inflacao_total
        except Exception as e:
            print(f"Erro ao somar valores: {e}")
            return None

    except json.JSONDecodeError as je:
        print(f"Erro ao decodificar JSON: {je}")
        return None
    except Exception as e:
        print(f"Erro ao pegar inflação: {e}")
        return None


def ajustar_inflacao(ipca_data, coluna_ipca, periodo_inicial, valor, data_final):
    """
    Ajustar um valor considerando a inflação acumulada entre um período inicial e uma data final.

    :param ipca_data: DataFrame com dados de inflação
    :param coluna_ipca: Nome da coluna da série temporal do IPCA no DataFrame
    :param periodo_inicial: Data inicial no formato 'YYYY-MM-DD'
    :param valor: Valor a ser ajustado
    :param data_final: Data final no formato 'YYYY-MM-DD'
    :return: Valor ajustado pela inflação
    """
    # Filtrar os dados para o período relevante
    df_ipca = ipca_data.loc[periodo_inicial:data_final].copy()

    # Calcular o fator de correção acumulado
    df_ipca['IPCA'] = df_ipca[coluna_ipca] / 100  # Converter porcentagem para fator decimal
    df_ipca['Fator de Correcao'] = (1 + df_ipca['IPCA']).cumprod()

    # Calcular o valor equivalente
    fator_correcao_final = df_ipca['Fator de Correcao'].iloc[-1]
    valor_equivalente = valor / fator_correcao_final

    return valor_equivalente
