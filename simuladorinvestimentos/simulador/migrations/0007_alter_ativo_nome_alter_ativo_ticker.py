# Generated by Django 5.0.6 on 2024-08-06 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulador', '0006_simulacaoautomatica_usuario_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ativo',
            name='nome',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='ativo',
            name='ticker',
            field=models.CharField(max_length=50),
        ),
    ]
