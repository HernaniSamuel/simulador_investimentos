from django.db import models

# Create your models here.

class Benchmark(models.Model):
    ticker = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    data_inicial_pesquisa = models.DateField()
    data_final_pesquisa = models.DateField()
    resultados = models.JSONField()
    moeda_base = models.CharField(max_length=10)


class Ativo(models.Model):
    ticker = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    peso = models.FloatField()
    posse = models.FloatField()
    data_inicial_pesquisa = models.DateField()
    data_final_pesquisa = models.DateField()
    precos = models.JSONField()
    rentabilidade_total = models.FloatField()


class Indicador(models.Model):
    nome = models.CharField(max_length=100)
    indice = models.FloatField()
    precos_da_carteira = models.JSONField()


class CarteiraAutomatica(models.Model):
    ativos = models.ManyToManyField(Ativo)
    valor_em_dinheiro = models.FloatField()
    valor_ativos = models.FloatField()
    indicadores = models.ManyToManyField(Indicador)
    moeda_base = models.CharField(max_length=10)


class CarteiraManual(models.Model):
    ativos = models.ManyToManyField(Ativo)
    valor_em_dinheiro = models.FloatField()
    valor_total = models.FloatField()
    valor_ativos = models.FloatField()
    indicadores = models.ManyToManyField()
    moeda_base = models.CharField(max_length=10)


class SimulacaoAutomatica(models.Model):
    nome = models.CharField(max_length=100)
    data_inicial = models.DateField()
    data_final = models.DateField()
    aplicacao_inicial = models.FloatField()
    aplicacao_mensal = models.FloatField()
    carteira_automatica = models.ForeignKey(CarteiraAutomatica, on_delete=models.CASCADE)
    mes_atual_de_simulacao = models.IntegerField()


class SimulacaoManual(models.Model):
    nome = models.CharField(max_length=100)
    data_inicial = models.DateField()
    data_final = models.DateField()
    mes_atual_de_simulacao = models.IntegerField()
    carteira_manual = models.ForeignKey(CarteiraManual, on_delete=models.CASCADE)


class Historico(models.Model):
    simulacao_manual = models.ForeignKey(SimulacaoManual, on_delete=models.CASCADE, null=True, blank=True)
    simulacao_automatica = models.ForeignKey(SimulacaoAutomatica, on_delete=models.CASCADE, null=True, blank=True)
    conferir_se_ha_simulacao_aberta = models.BooleanField(default=False)
