from datetime import datetime
import pandas as pd
from ..models import SimulacaoManual
from ..utils import arredondar_para_baixo, ajustar_inflacao


def modificar_dinheiro(simulacao_id, user, valor, ajustar_inflacao_flag):
    try:
        # Obtém a simulação correspondente
        simulacao = SimulacaoManual.objects.get(id=simulacao_id, usuario=user)
        carteira = simulacao.carteira_manual

        # Arredondar o valor
        valor = arredondar_para_baixo(valor)

        # Converter JSONField para DataFrame
        ipca_data_json = simulacao.inflacao_total  # Isso é um dicionário
        ipca_data = pd.DataFrame(ipca_data_json)

        # Verificar se 'Data' está nas colunas
        if 'Data' in ipca_data.columns:
            ipca_data['Data'] = pd.to_datetime(ipca_data['Data'])
            ipca_data.set_index('Data', inplace=True)
        else:
            return {'error': "A coluna 'Data' não está presente em ipca_data."}, 500

        coluna_ipca = "Valor"
        periodo_inicial = datetime.today().date()
        data_final = simulacao.mes_atual.date()

        # Se o valor for 0, não faz nada
        if valor == 0:
            return {'message': 'Nenhuma alteração foi feita, valor 0.'}, 400

        # Se o valor de valor_em_dinheiro for None, definimos como 0
        valor_atual_em_dinheiro = carteira.valor_em_dinheiro if carteira.valor_em_dinheiro is not None else 0

        # Se a checkbox estiver marcada, ajusta o valor usando a inflação
        if ajustar_inflacao_flag:
            valor_ajustado = ajustar_inflacao(ipca_data, coluna_ipca, periodo_inicial, valor, data_final)
            if valor_ajustado is None:
                return {'error': 'Erro ao ajustar o valor pela inflação.'}, 500
            valor = arredondar_para_baixo(valor_ajustado)

        # Modifica o valor em caixa da carteira
        novo_valor = valor_atual_em_dinheiro + valor

        # Impede que o novo valor seja negativo (mantém pelo menos zero)
        if novo_valor < 0:
            novo_valor = 0

        carteira.valor_em_dinheiro = arredondar_para_baixo(novo_valor)
        carteira.save()

        return {'message': 'Valor atualizado com sucesso.', 'novo_valor': novo_valor}, 200

    except SimulacaoManual.DoesNotExist:
        return {'error': 'Simulação não encontrada.'}, 404
    except Exception as e:
        return {'error': str(e)}, 500
