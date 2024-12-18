# Generated by Django 5.0.6 on 2024-07-31 16:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('simulador', '0002_remove_carteiraautomatica_ativos_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ativo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('nome', models.CharField(max_length=10)),
                ('peso', models.FloatField()),
                ('posse', models.FloatField()),
                ('precos', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Indicador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('nome', models.CharField(max_length=100)),
                ('indices', models.JSONField(default=dict)),
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
                ('nome', models.CharField(max_length=50)),
                ('data_inicial', models.DateField()),
                ('data_final', models.DateField()),
                ('aplicacao_inicial', models.FloatField()),
                ('aplicacao_mensal', models.FloatField()),
                ('carteira_automatica', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='simulador.carteiraautomatica')),
            ],
        ),
    ]
