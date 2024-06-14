# Generated by Django 5.0.6 on 2024-06-13 18:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ativo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('nome', models.CharField(max_length=100)),
                ('peso', models.FloatField()),
                ('posse', models.FloatField()),
                ('data_inicial_pesquisa', models.DateField()),
                ('data_final_pesquisa', models.DateField()),
                ('precos', models.JSONField()),
                ('rentabilidade_total', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Benchmark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('nome', models.CharField(max_length=100)),
                ('data_inicial_pesquisa', models.DateField()),
                ('data_final_pesquisa', models.DateField()),
                ('resultados', models.JSONField()),
                ('moeda_base', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Indicador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('indice', models.FloatField()),
                ('precos_da_carteira', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='CarteiraManual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_em_dinheiro', models.FloatField()),
                ('valor_total', models.FloatField()),
                ('valor_ativos', models.FloatField()),
                ('moeda_base', models.CharField(max_length=10)),
                ('ativos', models.ManyToManyField(to='simulador.ativo')),
                ('indicadores', models.ManyToManyField(to='simulador.indicador')),
            ],
        ),
        migrations.CreateModel(
            name='CarteiraAutomatica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_em_dinheiro', models.FloatField()),
                ('valor_ativos', models.FloatField()),
                ('moeda_base', models.CharField(max_length=10)),
                ('ativos', models.ManyToManyField(to='simulador.ativo')),
                ('indicadores', models.ManyToManyField(to='simulador.indicador')),
            ],
        ),
        migrations.CreateModel(
            name='SimulacaoAutomatica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('data_inicial', models.DateField()),
                ('data_final', models.DateField()),
                ('aplicacao_inicial', models.FloatField()),
                ('aplicacao_mensal', models.FloatField()),
                ('mes_atual_de_simulacao', models.IntegerField()),
                ('carteira_automatica', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulador.carteiraautomatica')),
            ],
        ),
        migrations.CreateModel(
            name='SimulacaoManual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('data_inicial', models.DateField()),
                ('data_final', models.DateField()),
                ('mes_atual_de_simulacao', models.IntegerField()),
                ('carteira_manual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulador.carteiramanual')),
            ],
        ),
        migrations.CreateModel(
            name='Historico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conferir_se_ha_simulacao_aberta', models.BooleanField(default=False)),
                ('simulacao_automatica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='simulador.simulacaoautomatica')),
                ('simulacao_manual', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='simulador.simulacaomanual')),
            ],
        ),
    ]
