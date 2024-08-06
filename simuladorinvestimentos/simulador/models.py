from django.db import models
from django.contrib.auth.models import User


class Ativo(models.Model):
    ticker = models.CharField(max_length=50)
    nome = models.CharField(max_length=100)
    peso = models.FloatField()
    posse = models.FloatField()
    precos = models.JSONField(default=dict)

    def __str__(self):
        return self.nome


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

    def __str__(self):
        return f"Carteira {self.id} - {self.moeda_base}"


class SimulacaoAutomatica(models.Model):
    nome = models.CharField(max_length=100)
    data_inicial = models.DateField()
    data_final = models.DateField()
    aplicacao_inicial = models.FloatField()
    aplicacao_mensal = models.FloatField()
    carteira_automatica = models.OneToOneField(CarteiraAutomatica, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Para relacionar a simulação ao usuário
    tipo = models.CharField(max_length=10)
    inflacao_total = models.JSONField(default=dict)
    resultados = models.JSONField(default=dict)

    def __str__(self):
        return self.nome


class Historico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    simulacoes = models.ManyToManyField(SimulacaoAutomatica)  # Mudando para ManyToManyField
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Histórico de {self.usuario.username} - {self.simulacoes.count()} simulações"
