# Generated by Django 4.1.3 on 2023-04-07 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ativos', '0011_ativo_un_atual_usd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ativo',
            name='custo_total',
            field=models.DecimalField(decimal_places=2, default=None, max_digits=14, null=True),
        ),
    ]
