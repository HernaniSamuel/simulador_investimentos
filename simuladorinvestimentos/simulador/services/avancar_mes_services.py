from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta
import yfinance as yf
from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo


def avancar_mes(simulacao_id, user):
    try:
        # Obtém a simulação e a carteira associada
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
        carteira_manual = simulacao.carteira_manual

        # Define o mês atual e o novo mês
        mes_atual = simulacao.mes_atual
        novo_mes = mes_atual + relativedelta(months=1)

        # Processa cada ativo na carteira
        ativos = carteira_manual.ativos.all()
        for ativo in ativos:
            try:
                yf_data = yf.Ticker(ativo.ticker)

                # Ajusta as datas para incluir o mês atual
                historico_precos = yf_data.history(
                    start=mes_atual.strftime('%Y-%m-%d'),
                    end=novo_mes.strftime('%Y-%m-%d'),  # 'end' é exclusivo
                    interval="1mo",
                    auto_adjust=False,  # Obtém preços não ajustados
                    actions=True       # Garante que os dados de dividendos sejam obtidos
                )

                if not historico_precos.empty:
                    # Formata o histórico de preços para o mês atual
                    novo_preco = {
                        str(index.date()): {
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close'])
                        }
                        for index, row in historico_precos.iterrows()
                    }

                    # Atualiza os preços no ativo
                    ativo.precos.update(novo_preco)
                    ativo.save()
                else:
                    print(f"{ativo.ticker}: No price data found for {mes_atual.strftime('%Y-%m')}.")

                # Processa os dividendos para o mês atual
                dividendos = yf_data.dividends
                if not dividendos.empty:
                    # Filtra os dividendos no mês atual
                    dividendos_mes = dividendos.loc[(dividendos.index >= mes_atual) & (dividendos.index < novo_mes)]
                    if not dividendos_mes.empty:
                        # Calcula o total de dividendos recebidos
                        total_dividendo = dividendos_mes.sum() * ativo.posse
                        total_dividendo_arredondado = arredondar_para_baixo(total_dividendo)

                        # Atualiza o valor em dinheiro na carteira
                        carteira_manual.valor_em_dinheiro += total_dividendo_arredondado
                        carteira_manual.save()

            except Exception as e:
                print(f"Erro ao processar ativo {ativo.ticker}: {e}")

        # Recalcula o valor total dos ativos após atualizar os preços
        ativos = carteira_manual.ativos.filter(posse__gt=0)
        valor_total_ativos = 0
        for ativo in ativos:
            precos_armazenados = ativo.precos
            mes_str = mes_atual.strftime('%Y-%m-%d')  # Usamos 'mes_atual' aqui
            preco_no_mes_data = precos_armazenados.get(mes_str, None)
            if preco_no_mes_data:
                preco_no_mes = preco_no_mes_data.get('close', 0)
            else:
                preco_no_mes = 0
            valor_ativo = ativo.posse * preco_no_mes
            valor_total_ativos += valor_ativo

        # Atualiza o histórico de valor total
        historico = simulacao.historico_valor_total or []
        historico.append(valor_total_ativos)
        simulacao.historico_valor_total = historico

        # Atualiza a simulação para o novo mês
        simulacao.mes_atual = novo_mes
        simulacao.save()

        return {
            'message': 'Simulação avançada para o próximo mês.',
            'mes_atual': novo_mes.strftime('%Y-%m-%d'),
        }, 200

    except SimulacaoManual.DoesNotExist:
        return {'error': 'Simulação não encontrada.'}, 404
    except Exception as e:
        return {'error': str(e)}, 500
