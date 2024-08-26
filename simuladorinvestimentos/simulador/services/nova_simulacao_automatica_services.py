from django.utils import timezone
from ..models import CarteiraAutomatica, SimulacaoAutomatica, Historico
from datetime import datetime
from ..utils import pegar_inflacao


def criar_simulacao_automatica(nome, data_inicial, data_final, aplicacao_inicial, aplicacao_mensal, moeda_base, usuario):
    inflacao_total = pegar_inflacao(start_date=data_inicial, end_date=datetime.today().strftime('%Y-%m-%d'))
    if inflacao_total is None:
        raise Exception('Failed to fetch inflation data')

    inflacao_total['Data'] = inflacao_total['Data'].dt.strftime('%Y-%m-%d')
    inflacao_dict = inflacao_total.to_dict(orient='records')

    carteira_automatica = CarteiraAutomatica.objects.create(
        valor_em_dinheiro=aplicacao_inicial,
        moeda_base=moeda_base,
        valor_ativos=0
    )

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

    historico, created = Historico.objects.get_or_create(
        usuario=usuario,
        defaults={'data_criacao': timezone.now()}
    )

    historico.simulacoes.add(simulacao_automatica)
    historico.save()

    return simulacao_automatica, carteira_automatica, inflacao_dict
