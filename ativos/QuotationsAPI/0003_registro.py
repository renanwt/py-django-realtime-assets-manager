# Generated by Django 4.1.3 on 2023-03-06 00:30

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ativos', '0002_ativo_custo_total_ativo_max_pago_ativo_min_pago'),
    ]

    operations = [
        migrations.CreateModel(
            name='Registro',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('moeda_utilizada', models.CharField(max_length=10)),
                ('custo_total', models.DecimalField(decimal_places=6, max_digits=10)),
                ('total_saida_brl', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('cotacao_sai_brl', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('total_saida_usd', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('cotacao_sai_usd', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('ativo_adquirido', models.CharField(max_length=10)),
                ('qtd_entrada', models.DecimalField(decimal_places=6, max_digits=10)),
                ('total_entrada_brl', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('cotacao_ent_brl', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('total_entrada_usd', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('cotacao_ent_usd', models.DecimalField(decimal_places=6, default=None, max_digits=10, null=True)),
                ('taxa', models.DecimalField(decimal_places=6, default=0, max_digits=10, null=True)),
                ('cambio_usd', models.FloatField(blank=True, default=0, null=True)),
                ('de_dividendos', models.BooleanField(blank=True, null=True)),
            ],
        ),
    ]