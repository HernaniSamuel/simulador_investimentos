from bcb import sgs


def pegar_inflacao(start_date, end_date):
    """
    Obter dados de inflação (IPCA) do Banco Central do Brasil.

    :param start_date: Data inicial no formato 'YYYY-MM-DD'
    :param end_date: Data final no formato 'YYYY-MM-DD'
    :return: DataFrame com dados de inflação
    """
    # Código da série temporal do IPCA no BCB
    codigo_ipca = 433

    # Obter os dados da série temporal
    ipca_data = sgs.get(codigo_ipca, start=start_date, end=end_date)

    return ipca_data, '433'  # Retorna o DataFrame e o nome da coluna como string


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
