from django.db import models
from django.contrib.auth.models import User


class Ativo(models.Model):
    ticker = models.CharField(max_length=50)
    nome = models.CharField(max_length=100)
    peso = models.FloatField()
    posse = models.FloatField()
    precos = models.JSONField(default=dict)
    ultimo_preco_convertido = models.FloatField()
    data_lancamento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nome


class CarteiraAutomatica(models.Model):
    ativos = models.ManyToManyField(Ativo)
    valor_em_dinheiro = models.FloatField()
    valor_ativos = models.FloatField()
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
    inflacao_total = models.JSONField(default=dict)
    resultados = models.JSONField(default=dict)

    def __str__(self):
        return self.nome


class CarteiraManual(models.Model):
    ativos = models.ManyToManyField(Ativo)
    valor_em_dinheiro = models.FloatField()
    valor_ativos = models.FloatField()
    moeda_base = models.CharField(max_length=10)

    def __str__(self):
        return f"Carteira {self.id} - {self.moeda_base}"


class SimulacaoManual(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Para relacionar a simulação ao usuário
    nome = models.CharField(max_length=100)
    data_inicial = models.DateField()
    mes_atual = models.DateTimeField()
    carteira_manual = models.OneToOneField(CarteiraManual, on_delete=models.CASCADE)
    inflacao_total = models.JSONField(default=dict)
    historico_valor_total = models.JSONField(default=list)


class Historico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    simulacoes_automaticas = models.ManyToManyField(SimulacaoAutomatica, blank=True)  # Relacionamento para Simulação Automática
    simulacoes_manuais = models.ManyToManyField(SimulacaoManual, blank=True)  # Relacionamento para Simulação Manual
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        total_simulacoes = self.simulacoes_automaticas.count() + self.simulacoes_manuais.count()
        return f"Histórico de {self.usuario.username} - {total_simulacoes} simulações"
