from django.utils import timezone
from ..models import CarteiraManual, SimulacaoManual, Historico
from datetime import datetime
from ..utils import pegar_inflacao


def criar_simulacao_manual(nome, data_inicial, moeda_base, usuario):
    inflacao_total = pegar_inflacao(start_date=data_inicial, end_date=datetime.today().strftime('%Y-%m-%d'))
    if inflacao_total is None:
        raise Exception('Failed to fetch inflation data')

    inflacao_total['Data'] = inflacao_total['Data'].dt.strftime('%Y-%m-%d')
    inflacao_dict = inflacao_total.to_dict(orient='records')

    carteira_manual = CarteiraManual.objects.create(
        valor_em_dinheiro=0,
        moeda_base=moeda_base,
        valor_ativos=0
    )

    simulacao_manual = SimulacaoManual.objects.create(
        nome=nome,
        data_inicial=data_inicial,
        carteira_manual=carteira_manual,
        usuario=usuario,
        inflacao_total=inflacao_dict,
        mes_atual=data_inicial
    )

    historico, created = Historico.objects.get_or_create(
        usuario=usuario,
        defaults={'data_criacao': timezone.now()}
    )

    historico.simulacoes_manuais.add(simulacao_manual)
    historico.save()

    return simulacao_manual, carteira_manual
