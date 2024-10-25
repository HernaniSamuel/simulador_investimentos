from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta
import yfinance as yf
import json
from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo

def avancar_mes(simulacao_id, user):
    try:
        print(f"Iniciando o avanço do mês para a simulação ID: {simulacao_id}, usuário: {user}")
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
        carteira_manual = simulacao.carteira_manual
        print(f"Simulação e carteira obtidas com sucesso. Mês atual: {simulacao.mes_atual}")

        mes_atual = simulacao.mes_atual
        novo_mes = mes_atual + relativedelta(months=1)
        print(f"Avançando o mês de {mes_atual} para {novo_mes}")

        moeda_base_carteira = carteira_manual.moeda_base
        print(f"Moeda base da carteira: {moeda_base_carteira}")

        ativos = carteira_manual.ativos.all()
        for ativo in ativos:
            try:
                print(f"Processando ativo: {ativo.ticker}")
                yf_data = yf.Ticker(ativo.ticker)

                info_ativo = yf_data.fast_info if hasattr(yf_data, 'fast_info') else yf_data.info
                moeda_base_ativo = info_ativo.get('currency', None)
                print(f"Moeda base do ativo {ativo.ticker}: {moeda_base_ativo}")

                inicio_mes = mes_atual.strftime('%Y-%m-%d')
                fim_mes = novo_mes.strftime('%Y-%m-%d')
                print(f"Obtendo histórico de preços para o intervalo: {inicio_mes} - {fim_mes}")

                historico_precos = yf_data.history(
                    start=inicio_mes,
                    end=fim_mes,
                    interval="1d",
                    auto_adjust=False
                )

                if not historico_precos.empty:
                    print(f"Histórico de preços obtido para {ativo.ticker}")
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
                    print(f"Histórico de preços atualizado para o ativo {ativo.ticker}")

                    preco_mes_atual = historico_precos['Close'].iloc[-1]  # Usa o último preço de fechamento disponível
                else:
                    preco_mes_atual = ativo.ultimo_preco_convertido or 0
                    print(f"Preços não encontrados para {ativo.ticker} no mês {mes_atual.strftime('%Y-%m')}. Usando último preço conhecido: {preco_mes_atual}")

                if moeda_base_ativo and moeda_base_ativo != moeda_base_carteira:
                    print(f"Moeda do ativo {moeda_base_ativo} é diferente da moeda da carteira {moeda_base_carteira}. Obtendo taxa de conversão.")
                    par_moedas = f"{moeda_base_ativo}{moeda_base_carteira}=X"
                    conversao_moeda = yf.Ticker(par_moedas)
                    historico_conversao = conversao_moeda.history(
                        start=inicio_mes,
                        end=fim_mes,
                        interval="1d"
                    )

                    if not historico_conversao.empty:
                        taxa_conversao = historico_conversao['Close'].iloc[-1]  # Usa a taxa de conversão mais recente
                        preco_mes_atual_convertido = preco_mes_atual * taxa_conversao
                        print(f"Taxa de conversão para {par_moedas}: {taxa_conversao}. Preço convertido: {preco_mes_atual_convertido}")
                    else:
                        print(f"Taxa de conversão não encontrada para {moeda_base_ativo} para {moeda_base_carteira} no mês {mes_atual.strftime('%Y-%m')}. Usando o preço sem conversão.")
                        preco_mes_atual_convertido = preco_mes_atual
                else:
                    preco_mes_atual_convertido = preco_mes_atual
                    print(f"Moeda do ativo e da carteira são iguais. Preço não necessita de conversão: {preco_mes_atual_convertido}")

                preco_mes_atual_convertido = arredondar_para_baixo(preco_mes_atual_convertido)
                print(f"Preço convertido após arredondamento: {preco_mes_atual_convertido}")

                ativo.ultimo_preco_convertido = preco_mes_atual_convertido
                ativo.save()
                print(f"Ativo {ativo.ticker} atualizado com sucesso.")

            except Exception as e:
                print(f"Erro ao buscar preços para {ativo.ticker}: {e}")

        ativos = carteira_manual.ativos.filter(posse__gt=0)
        valor_total_ativos = 0
        for ativo in ativos:
            preco_no_mes = ativo.ultimo_preco_convertido or 0
            valor_ativo = arredondar_para_baixo(ativo.posse * preco_no_mes)
            valor_total_ativos += valor_ativo
            print(f"Valor do ativo {ativo.ticker}: {valor_ativo}. Valor total acumulado: {valor_total_ativos}")

        valor_total_ativos = arredondar_para_baixo(valor_total_ativos)
        print(f"Valor total dos ativos após arredondamento: {valor_total_ativos}")

        if simulacao.historico_valor_total:
            historico = json.loads(simulacao.historico_valor_total)
        else:
            historico = []

        historico.append(valor_total_ativos)
        simulacao.historico_valor_total = json.dumps(historico)
        print(f"Histórico de valor total atualizado: {historico}")

        simulacao.mes_atual = novo_mes
        simulacao.save()
        print(f"Simulação avançada para o próximo mês: {novo_mes}")

        return {
            'message': 'Simulação avançada para o próximo mês.',
            'mes_atual': novo_mes.strftime('%Y-%m-%d'),
        }, 200

    except Exception as e:
        print(f"Erro ao avançar o mês para a simulação {simulacao_id}: {e}")
        return {'error': str(e)}, 500
