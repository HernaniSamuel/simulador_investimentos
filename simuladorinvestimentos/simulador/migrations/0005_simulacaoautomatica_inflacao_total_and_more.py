# Generated by Django 5.0.6 on 2024-08-02 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulador', '0004_simulacaoautomatica_tipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulacaoautomatica',
            name='inflacao_total',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='simulacaoautomatica',
            name='resultados',
            field=models.JSONField(default=dict),
        ),
    ]
