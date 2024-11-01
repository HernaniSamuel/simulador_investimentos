from django.utils import timezone

from ..models import CarteiraManual, SimulacaoManual, Historico
from ..utils import pegar_inflacao

from datetime import datetime



def criar_simulacao_manual(nome, data_inicial, moeda_base, usuario):
    """
    Cria uma simulação manual de investimentos para um usuário.

    Args:
        nome (str): Nome da simulação.
        data_inicial (str): Data inicial da simulação no formato 'YYYY-MM-DD'.
        moeda_base (str): Moeda base da simulação.
        usuario (User): Usuário que está criando a simulação.

    Returns:
        tuple: Objeto da simulação manual e da carteira manual criados.
    """
    # Obter os dados de inflação desde a data inicial até hoje
    inflacao_total = pegar_inflacao(start_date=data_inicial, end_date=datetime.today().strftime('%Y-%m-%d'))
    if inflacao_total is None:
        raise Exception('Failed to fetch inflation data')

    # Formatar a data no DataFrame de inflação e converter para um dicionário
    inflacao_total['Data'] = inflacao_total['Data'].dt.strftime('%Y-%m-%d')
    inflacao_dict = inflacao_total.to_dict(orient='records')

    # Criar a carteira manual associada à simulação
    carteira_manual = CarteiraManual.objects.create(
        valor_em_dinheiro=0,
        moeda_base=moeda_base,
        valor_ativos=0
    )

    # Criar a simulação manual com as informações fornecidas
    simulacao_manual = SimulacaoManual.objects.create(
        nome=nome,
        data_inicial=data_inicial,
        carteira_manual=carteira_manual,
        usuario=usuario,
        inflacao_total=inflacao_dict,
        mes_atual=data_inicial
    )

    # Obter ou criar o histórico do usuário e associar a nova simulação manual
    historico, created = Historico.objects.get_or_create(
        usuario=usuario,
        defaults={'data_criacao': timezone.now()}
    )

    # Adicionar a simulação ao histórico do usuário
    historico.simulacoes_manuais.add(simulacao_manual)
    historico.save()

    return simulacao_manual, carteira_manual
