# Generated by Django 5.0.6 on 2024-09-23 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulador', '0008_remove_historico_simulacao_historico_simulacoes'),
    ]

    operations = [
        migrations.AddField(
            model_name='ativo',
            name='data_lancamento',
            field=models.DateField(blank=True, null=True),
        ),
    ]
