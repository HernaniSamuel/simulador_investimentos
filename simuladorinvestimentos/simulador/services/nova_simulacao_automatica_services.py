from django.utils import timezone

from ..models import CarteiraAutomatica, SimulacaoAutomatica, Historico
from datetime import datetime
from ..utils import pegar_inflacao


def criar_simulacao_automatica(nome, data_inicial, data_final, aplicacao_inicial, aplicacao_mensal, moeda_base, usuario):
    """
    Cria uma simulação automática de investimentos para um usuário.

    Args:
        nome (str): Nome da simulação.
        data_inicial (str): Data inicial da simulação no formato 'YYYY-MM-DD'.
        data_final (str): Data final da simulação no formato 'YYYY-MM-DD'.
        aplicacao_inicial (float): Valor da aplicação inicial.
        aplicacao_mensal (float): Valor da aplicação mensal.
        moeda_base (str): Moeda base da simulação.
        usuario (User): Usuário que está criando a simulação.

    Returns:
        tuple: Objeto da simulação automática e da carteira automática criados.
    """
    # Obter os dados de inflação desde a data inicial até a data atual
    inflacao_total = pegar_inflacao(start_date=data_inicial, end_date=datetime.today().strftime('%Y-%m-%d'))
    if inflacao_total is None:
        raise Exception('Falha ao buscar dados de inflação')

    # Formatar a data no DataFrame de inflação e converter para um dicionário
    inflacao_total['Data'] = inflacao_total['Data'].dt.strftime('%Y-%m-%d')
    inflacao_dict = inflacao_total.to_dict(orient='records')

    # Criar a carteira automática associada à simulação
    carteira_automatica = CarteiraAutomatica.objects.create(
        valor_em_dinheiro=aplicacao_inicial,
        moeda_base=moeda_base,
        valor_ativos=0
    )

    # Criar a simulação automática com as informações fornecidas
    simulacao_automatica = SimulacaoAutomatica.objects.create(
        nome=nome,
        data_inicial=data_inicial,
        data_final=data_final,
        aplicacao_inicial=aplicacao_inicial,
        aplicacao_mensal=aplicacao_mensal,
        carteira_automatica=carteira_automatica,
        usuario=usuario,
        inflacao_total=inflacao_dict
    )

    # Obter ou criar o histórico do usuário e associar a nova simulação automática
    historico, created = Historico.objects.get_or_create(
        usuario=usuario,
        defaults={'data_criacao': timezone.now()}
    )

    # Adicionar a simulação ao histórico do usuário
    historico.simulacoes_automaticas.add(simulacao_automatica)
    historico.save()

    return simulacao_automatica, carteira_automatica
