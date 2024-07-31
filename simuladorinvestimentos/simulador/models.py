from django.db import models

from .utils import pesquisar_precos

class Ativo(models.Model):
    ticker = models.CharField(max_length=10)
    nome = models.CharField(max_length=10)
    peso = models.FloatField()
    posse = models.FloatField()
    precos = models.JSONField(default=dict)


class Indicador(models.Model):
    ticker = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    indices = models.JSONField(default=dict)


class CarteiraAutomatica(models.Model):
    ativos = models.ManyToManyField(Ativo)
    valor_em_dinheiro = models.FloatField()
    valor_ativos = models.FloatField()
    indicadores = models.ManyToManyField(Indicador)
    moeda_base = models.CharField(max_length=10)

    def comprar_ativos(self):
        pass

    def calcular_valor_ativos(self):
        pass



class SimulacaoAutomatica(models.Model):
    nome = models.CharField(max_length=50)
    data_inicial = models.DateField()
    data_final = models.DateField()
    aplicacao_inicial = models.FloatField()
    aplicacao_mensal = models.FloatField()
    carteira_automatica = models.OneToOneField(CarteiraAutomatica, on_delete=models.CASCADE)

    def iterar_tempo(self):
        pass

