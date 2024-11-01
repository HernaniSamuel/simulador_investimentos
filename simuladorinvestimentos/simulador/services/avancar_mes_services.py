import json
import yfinance as yf

from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta

from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo


def avancar_mes(simulacao_id, user):
    """
    Avança o mês de uma simulação manual, atualizando os ativos, dividendos e histórico da carteira.

    Args:
        simulacao_id (int): ID da simulação manual a ser atualizada.
        user (User): Usuário autenticado realizando a operação.

    Returns:
        tuple: Dicionário de resposta e código de status HTTP.
    """
    try:
        # Obter simulação e carteira manual
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
        carteira_manual = simulacao.carteira_manual

        # Avançar para o próximo mês
        mes_atual = simulacao.mes_atual
        novo_mes = mes_atual + relativedelta(months=1)
        moeda_base_carteira = carteira_manual.moeda_base

        ativos = carteira_manual.ativos.all()
        for ativo in ativos:
            try:
                # Obter informações do ativo do yfinance
                yf_data = yf.Ticker(ativo.ticker)
                info_ativo = yf_data.info
                moeda_base_ativo = info_ativo.get('currency', None)

                # Definir o intervalo do mês para buscar dados
                inicio_mes = mes_atual.strftime('%Y-%m-%d')
                fim_mes = novo_mes.strftime('%Y-%m-%d')

                # Obter histórico de preços para o mês
                historico_precos = yf_data.history(start=inicio_mes, end=fim_mes, interval="1d", auto_adjust=False)

                # Processar dividendos
                dividends = yf_data.dividends
                if not dividends.empty:
                    filtered_dividends = dividends[(dividends.index >= inicio_mes) & (dividends.index < fim_mes)]
                    if not filtered_dividends.empty:
                        dividend_value = filtered_dividends.sum() * ativo.posse

                        # Converter dividendos se necessário
                        if moeda_base_ativo and moeda_base_ativo != moeda_base_carteira:
                            par_moedas = f"{moeda_base_ativo}{moeda_base_carteira}=X"
                            conversao_moeda = yf.Ticker(par_moedas)
                            historico_conversao = conversao_moeda.history(start=inicio_mes, end=fim_mes, interval="1d")

                            if not historico_conversao.empty:
                                taxa_conversao = historico_conversao['Close'].iloc[-1]
                                dividend_value_convertido = dividend_value * taxa_conversao
                            else:
                                dividend_value_convertido = dividend_value
                        else:
                            dividend_value_convertido = dividend_value

                        # Somar dividendos ao valor em dinheiro da carteira
                        carteira_manual.valor_em_dinheiro += arredondar_para_baixo(dividend_value_convertido)
                        carteira_manual.save()

                # Processar histórico de preços do ativo
                if not historico_precos.empty:
                    precos = ativo.precos if ativo.precos else {}
                    for index, row in historico_precos.iterrows():
                        data_preco = index.strftime('%Y-%m-%d')
                        precos[data_preco] = {
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close'])
                        }
                    ativo.precos = precos
                    preco_mes_atual = historico_precos['Close'].iloc[-1]
                else:
                    preco_mes_atual = ativo.ultimo_preco_convertido or 0

                # Converter preço se necessário
                if moeda_base_ativo and moeda_base_ativo != moeda_base_carteira:
                    par_moedas = f"{moeda_base_ativo}{moeda_base_carteira}=X"
                    conversao_moeda = yf.Ticker(par_moedas)
                    historico_conversao = conversao_moeda.history(start=inicio_mes, end=fim_mes, interval="1d")

                    if not historico_conversao.empty:
                        taxa_conversao = historico_conversao['Close'].iloc[-1]
                        preco_mes_atual_convertido = preco_mes_atual * taxa_conversao
                    else:
                        preco_mes_atual_convertido = preco_mes_atual
                else:
                    preco_mes_atual_convertido = preco_mes_atual

                preco_mes_atual_convertido = arredondar_para_baixo(preco_mes_atual_convertido)
                ativo.ultimo_preco_convertido = preco_mes_atual_convertido
                ativo.save()

            except Exception as e:
                return {'error': f'Erro ao buscar preços para o ativo {ativo.ticker}: {str(e)}'}, 500

        # Atualizar valor total dos ativos na carteira
        ativos = carteira_manual.ativos.filter(posse__gt=0)
        valor_total_ativos = sum(arredondar_para_baixo(ativo.posse * (ativo.ultimo_preco_convertido or 0)) for ativo in ativos)
        valor_total_ativos = arredondar_para_baixo(valor_total_ativos)

        # Atualizar histórico do valor total da carteira
        historico = json.loads(simulacao.historico_valor_total) if simulacao.historico_valor_total else []
        historico.append(valor_total_ativos)
        simulacao.historico_valor_total = json.dumps(historico)

        # Avançar o mês da simulação
        simulacao.mes_atual = novo_mes
        simulacao.save()

        return {
            'message': 'Simulação avançada para o próximo mês.',
            'mes_atual': novo_mes.strftime('%Y-%m-%d'),
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500
