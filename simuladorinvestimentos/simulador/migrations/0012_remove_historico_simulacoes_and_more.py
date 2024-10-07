# Generated by Django 5.0.6 on 2024-10-01 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulador', '0011_simulacaomanual_inflacao_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historico',
            name='simulacoes',
        ),
        migrations.AddField(
            model_name='historico',
            name='simulacoes_automaticas',
            field=models.ManyToManyField(blank=True, to='simulador.simulacaoautomatica'),
        ),
        migrations.AddField(
            model_name='historico',
            name='simulacoes_manuais',
            field=models.ManyToManyField(blank=True, to='simulador.simulacaomanual'),
        ),
    ]