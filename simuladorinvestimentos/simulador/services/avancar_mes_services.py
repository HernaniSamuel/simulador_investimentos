from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta
import yfinance as yf
import json
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

        # Moeda base da carteira
        moeda_base_carteira = carteira_manual.moeda_base  # Certifique-se de que este campo existe

        # Processa cada ativo na carteira
        ativos = carteira_manual.ativos.all()
        for ativo in ativos:
            try:
                yf_data = yf.Ticker(ativo.ticker)

                # Obtém a moeda base do ativo usando o yfinance
                info_ativo = yf_data.info
                moeda_base_ativo = info_ativo.get('currency', None)

                # Define o intervalo para obter os preços do mês inteiro
                inicio_mes = mes_atual.strftime('%Y-%m-%d')
                fim_mes = novo_mes.strftime('%Y-%m-%d')  # 'end' é exclusivo

                # Obtém o histórico de preços do mês
                historico_precos = yf_data.history(
                    start=inicio_mes,
                    end=fim_mes,
                    interval="1d",
                    auto_adjust=False,
                    actions=False
                )

                if not historico_precos.empty:
                    # Atualiza o histórico de preços do ativo
                    # Carrega o ativo.precos existente
                    if ativo.precos:
                        precos = ativo.precos
                    else:
                        precos = {}

                    # Adiciona os preços do mês ao histórico
                    for index, row in historico_precos.iterrows():
                        data_preco = index.strftime('%Y-%m-%d')
                        precos[data_preco] = {
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close'])
                        }

                    # Atualiza o ativo.precos
                    ativo.precos = precos

                    # Usa o preço médio do mês para o cálculo do valor total
                    preco_mes_atual = historico_precos['Close'].mean()
                else:
                    # Se o histórico estiver vazio, mantém o último preço conhecido
                    preco_mes_atual = ativo.ultimo_preco_convertido or 0
                    print(f"Preços não encontrados para {ativo.ticker} no mês {mes_atual.strftime('%Y-%m')}. Usando último preço conhecido.")

                # Verifica se a moeda base do ativo é diferente da moeda base da carteira
                if moeda_base_ativo and moeda_base_ativo != moeda_base_carteira:
                    # Obter a cotação de conversão entre as moedas
                    par_moedas = f"{moeda_base_ativo}{moeda_base_carteira}=X"
                    conversao_moeda = yf.Ticker(par_moedas)
                    historico_conversao = conversao_moeda.history(
                        start=inicio_mes,
                        end=fim_mes,
                        interval="1d"
                    )

                    if not historico_conversao.empty:
                        # Usa a taxa média de conversão do mês
                        taxa_conversao = historico_conversao['Close'].mean()
                        preco_mes_atual_convertido = preco_mes_atual * taxa_conversao
                    else:
                        print(f"Taxa de conversão não encontrada para {moeda_base_ativo} para {moeda_base_carteira} no mês {mes_atual.strftime('%Y-%m')}. Usando o preço sem conversão.")
                        preco_mes_atual_convertido = preco_mes_atual  # Mantém o preço sem conversão se não houver taxa
                else:
                    preco_mes_atual_convertido = preco_mes_atual  # Não precisa converter se a moeda base for a mesma

                # Arredonda o preço convertido para evitar flutuações indesejadas
                preco_mes_atual_convertido = arredondar_para_baixo(preco_mes_atual_convertido)

                # Atualiza o preço convertido do ativo
                ativo.ultimo_preco_convertido = preco_mes_atual_convertido

                # Salva as alterações no ativo
                ativo.save()

            except Exception as e:
                print(f"Erro ao buscar preços para {ativo.ticker}: {e}")
                # Você pode optar por usar o último preço ou outra estratégia

        # Recalcula o valor total dos ativos após atualizar os preços
        ativos = carteira_manual.ativos.filter(posse__gt=0)
        valor_total_ativos = 0
        for ativo in ativos:
            preco_no_mes = ativo.ultimo_preco_convertido or 0
            valor_ativo = arredondar_para_baixo(ativo.posse * preco_no_mes)
            valor_total_ativos += valor_ativo

        # Arredonda o valor total dos ativos para baixo
        valor_total_ativos = arredondar_para_baixo(valor_total_ativos)

        # Atualiza o histórico de valor total
        if simulacao.historico_valor_total:
            historico = json.loads(simulacao.historico_valor_total)
        else:
            historico = []

        historico.append(valor_total_ativos)
        simulacao.historico_valor_total = json.dumps(historico)

        # Avança o mês na simulação
        simulacao.mes_atual = novo_mes
        simulacao.save()

        # Retorna a resposta e o status code
        return {
            'message': 'Simulação avançada para o próximo mês.',
            'mes_atual': novo_mes.strftime('%Y-%m-%d'),
        }, 200

    except Exception as e:
        print(f"Erro ao avançar o mês para a simulação {simulacao_id}: {e}")
        return {'error': str(e)}, 500
