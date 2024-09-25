import json
import pandas as pd
from datetime import datetime
from ..models import SimulacaoAutomatica
from ..utils import ajustar_inflacao
from dateutil.relativedelta import relativedelta


def safe_strptime(date_str, format='%Y-%m-%d'):
    try:
        return datetime.strptime(date_str, format).date()
    except ValueError:
        return None


def calcular_resultado_simulacao(simulacao_id):
    try:
        simulacao = SimulacaoAutomatica.objects.get(id=simulacao_id)

        ipca_data = pd.DataFrame(simulacao.inflacao_total)
        ipca_data['Data'] = pd.to_datetime(ipca_data['Data'], format='%Y-%m-%d')
        ipca_data.set_index('Data', inplace=True)

        data_inicial = pd.to_datetime(simulacao.data_inicial)
        data_final = pd.to_datetime(simulacao.data_final)

        data_final = data_final + relativedelta(months=1)

        if data_inicial is None or data_final is None:
            return {'error': 'Formato de data inválido'}, 400

        aplicacao_inicial_ajustada = ajustar_inflacao(
            periodo_inicial=data_inicial,
            ipca_data=ipca_data,
            coluna_ipca='Valor',
            valor=simulacao.aplicacao_inicial,
            data_final=data_final
        ) or 0
        # print(f'\033[1;33mAplicação inicial ajustada pela inflação: {aplicacao_inicial_ajustada}\033[m')

        aplicacoes_mensais_ajustadas = []
        datas_validas = ipca_data.loc[
            (ipca_data.index >= data_inicial) & (ipca_data.index <= data_final)].index

        for data_corrente in datas_validas:
            aplicacao_mensal_ajustada = ajustar_inflacao(
                periodo_inicial=data_corrente,
                ipca_data=ipca_data,
                coluna_ipca='Valor',
                valor=simulacao.aplicacao_mensal,
                data_final=data_final
            ) or 0
            aplicacoes_mensais_ajustadas.append(aplicacao_mensal_ajustada)
            # print(f'\033[1;33mAplicações mensais ajustadas pela inflação: {aplicacoes_mensais_ajustadas}\033[m')

        ativos = list(simulacao.carteira_automatica.ativos.all())
        adjclose_carteira = []
        valor_total_carteira = aplicacao_inicial_ajustada

        for mes_index, data_corrente in enumerate(datas_validas):
            # Adiciona a aplicação mensal ajustada
            valor_total_carteira += aplicacoes_mensais_ajustadas[mes_index]
            valor_inicial_mes = valor_total_carteira
            # print(f'\033[1;33mValor inicial no mês {data_corrente}: {valor_inicial_mes}\033[m')
            for ativo in ativos:
                # Verifica se o ativo já foi lançado no mês corrente
                if ativo.data_lancamento and data_corrente >= pd.Timestamp(ativo.data_lancamento):
                    precos = json.loads(ativo.precos)
                    # print(f'\033[1;33mPreços carregados: {precos}\033[m')
                    # Calcula o índice relativo ao ativo
                    meses_desde_lancamento = (data_corrente.year - pd.Timestamp(ativo.data_lancamento).year) * 12 + (
                                data_corrente.month - pd.Timestamp(ativo.data_lancamento).month)

                    if meses_desde_lancamento < len(precos):
                        preco_ativo = precos[meses_desde_lancamento]['Adj Close']
                        # print(f'\033[1;33mpreco_ativo: {preco_ativo}\033[m')
                        if preco_ativo > 0:
                            valor_investido = valor_inicial_mes * ativo.peso
                            # print(f'\033[1;33mValor investido: {valor_investido}\033[m')
                            quantidade_comprada = valor_investido / preco_ativo
                            # print(f'\033[1;33mQuantidade comprada: {quantidade_comprada}\033[m')
                            ativo.posse += quantidade_comprada
                            # print(f'\033[1;33mPosse do ativo: {ativo.posse}\033[m')
                            valor_total_carteira -= valor_investido
                            # print(f'\033[1;33mValor total da carteira: {valor_total_carteira}\033[m')
                        else:
                            print(
                                f"Alerta: Preço zero ou negativo detectado para {ativo.nome} no mês {meses_desde_lancamento}")
                    else:
                        pass
                        # print(f"Alerta: {ativo.nome} não existia no mês {meses_desde_lancamento}. Dinheiro mantido na conta.")
                else:
                    pass
                    # print(f"{ativo.nome} ainda não existia no mês {data_corrente}. Dinheiro mantido na conta.")

            # Calcula o valor da carteira com base no valor atual dos ativos
            valor_total_ativos_mes = sum(
                a.posse * json.loads(a.precos)[(data_corrente.year - pd.Timestamp(a.data_lancamento).year) * 12 + (
                            data_corrente.month - pd.Timestamp(a.data_lancamento).month)]['Adj Close']
                for a in ativos
                if a.data_lancamento and data_corrente >= pd.Timestamp(a.data_lancamento)
                and (data_corrente.year - pd.Timestamp(a.data_lancamento).year) * 12 + (
                            data_corrente.month - pd.Timestamp(a.data_lancamento).month) < len(json.loads(a.precos))
            )
            # print(f'\033[1;33mValor total de ativos no mês: {valor_total_ativos_mes}\033[m')

            valor_total_carteira_mes = valor_total_ativos_mes + valor_total_carteira
            # print(f'\033[1;33mValor total da carteira no mês: {valor_total_carteira_mes}\033[m')
            adjclose_carteira.append((data_corrente, valor_total_carteira_mes))
            # print(f'\033[1;33mAdjclose carteira: {adjclose_carteira}\033[m')

        print(f'último mês de adjclose_carteira: {adjclose_carteira[-1]}')
        # Criar um DataFrame com as datas e valores correspondentes
        df_resultado = pd.DataFrame(adjclose_carteira, columns=['Data', 'Valor'])

        # Convertendo as datas para strings antes de salvar
        df_resultado['Data'] = df_resultado['Data'].dt.strftime('%Y-%m-%d')

        # Convertendo adjclose_carteira para um formato JSON
        simulacao.resultados = df_resultado.to_dict(orient='records')

        # Coletar informações dos ativos
        ativos_info = [
            {
                'nome': ativo.nome,
                'ticker': ativo.ticker,
                'peso': ativo.peso,
                'posse': ativo.posse
            }
            for ativo in ativos
        ]

        # Estruturar a resposta JSON
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

        # Save the simulation with the updated results
        simulacao.save()

        # Save changes if necessary
        for ativo in ativos:
            # print(f'\033[1;32mPosse correta: {ativo.posse}')
            # print(f'\033[1;32m Antepenúltimo preço: {ativo.precos[-3]}, penúltimo preço: {ativo.precos[-2]}, último preço: {ativo.precos[-1]}\033[m')
            ativo.save()

        return resposta, 200

    except SimulacaoAutomatica.DoesNotExist:
        return {'error': 'SimulacaoAutomatica not found'}, 404
    except Exception as e:
        print(f'Erro durante a simulação: {str(e)}')
        return {'error': str(e)}, 500
