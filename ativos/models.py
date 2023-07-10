from django.db import models
from django.db.models import Sum
from django.utils import timezone
from .Base.models import BaseModel, QuerySet
from .QuotationsAPI.utils import to_usd, quotation_brl, quotation_usd, USD, to_brl


class Ativo(BaseModel):
    class classe(models.TextChoices):
        Acoes = 'ações', ('Ações_BR')
        FIIs = 'fiis', ('Fundos Imobiliários')
        Stocks = 'stocks', ('Stocks')
        REITs = 'reits', ('Reits americanos')
        Cryptos = 'cryptos', ('Criptoativos')
        ETF_BR = 'etfs_br', ('ETF BR')
        ETF_US = 'etf_us', ('ETF US')
        Caixa = 'caixa', ('Caixa')

    classe = models.CharField(max_length=10, choices=classe.choices, default=classe.Caixa)
    nome = models.CharField(max_length=10)
    quantidade = models.DecimalField(max_digits=14, decimal_places=6, default=None, null=True)
    pm_un = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    total_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    min_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    max_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    total_atual_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    perc_grupo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    un_atual_brl = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    un_atual_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    perc_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    lucro_preju = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    lucro_preju_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    perc_lucro = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)

    def save(self, *args, **kwargs):
        # valor unitário atualizado
        if self.classe == 'caixa' and self.nome == 'BRL':
            self.un_atual_brl = 1
            self.un_atual_usd = USD
        elif self.classe == 'caixa' and self.nome == 'USD':
            self.un_atual_usd = 1
            self.un_atual_brl = to_brl(1)
        else:
            self.un_atual_brl = quotation_brl(self.classe, self.nome)
            self.un_atual_usd = quotation_usd(self.classe, self.nome)

        # cálculo do custo total
        if self.pk is None and self.quantidade is not None and self.classe != 'caixa':
            self.custo_total = float(self.pm_un) * float(self.quantidade)

        # cálculo do valor total atual do ativo x em carteira (o do caixa será a soma dos inputados via request)
        if self.classe != 'caixa':
            self.total_atual = float(quotation_brl(self.classe, self.nome)) * float(self.quantidade)
            self.total_atual_usd = to_usd(self.total_atual)

        # valor total do ativo em usd
        self.total_atual_usd = to_usd(self.total_atual)

        # lucro ou prejuízo desse ativo em carteira
        if self.classe != 'caixa':
            self.lucro_preju = float(self.total_atual) - float(self.custo_total)
            self.lucro_preju_usd = to_usd(self.lucro_preju)

        # percentual com relação à própria classe
        if self.classe:
            sum_total_atual_class = Ativo.objects.filter(classe=self.classe).aggregate(Sum('total_atual'))['total_atual__sum']
            if sum_total_atual_class is not None:
                self.perc_grupo = float(self.total_atual) / float(sum_total_atual_class)

        # percentual com relação ao total
        sum_total_atual = Ativo.objects.filter(presente=True).aggregate(Sum('total_atual'))['total_atual__sum']
        if sum_total_atual is not None:
            self.perc_total = float(self.total_atual) / float(sum_total_atual)

        # lucro percentual do ativo
        self.perc_lucro = float(self.lucro_preju)*100 / float(self.custo_total)

        super(Ativo, self).save(*args, **kwargs)

    objects = QuerySet.as_manager()

    ''' classe = ações, fiis, etc
        nome = nome do ativo
        pm_un = preço médio
        valor_atual = valor de um único ativo após o fechamento do último dia útil
        lucro_prejo = valor nominal em reais do lucro ou prejuízo
        min_pago = preço mínimo pago por ativo
        max_pago = preço máximo pago por ativo
        percentual_classe = % total com relação à classe
        percentual_lucro = lucro ou prejuízo percentual
        saldo_USD = saldo convertido pra USD
        pm_USD = preço médio em USD
        valor_atual_USD = valor de um único ativo em USD
        percentual_patrimonio = percentual com o total do patrimônio.'''


class Patrimonio(BaseModel):
    patrimonio = models.FloatField(null=True, blank=True, default=0)
    patrimonio_usd = models.FloatField(null=True, blank=True, default=0)
    classes_percent = models.JSONField(default=dict, blank=True)
    classes_values = models.JSONField(default=dict, blank=True)
    assets_percent = models.JSONField(default=dict, blank=True)
    assets_values = models.JSONField(default=dict, blank=True)
    # acoes = models.FloatField(null=True, blank=True, default=0)
    # percentual_acoes = models.CharField(max_length=10, null=True, blank=True, default='')
    # fiis = models.FloatField(null=True, blank=True, default=0)
    # percentual_fiis = models.CharField(max_length=10, null=True, blank=True, default='')
    # stocks = models.FloatField(null=True, blank=True, default=0)
    # percentual_stocks = models.CharField(max_length=10, null=True, blank=True, default='')
    # reits = models.FloatField(null=True, blank=True, default=0)
    # percentual_reits = models.CharField(max_length=10, null=True, blank=True, default='')
    # Cryptos = models.FloatField(null=True, blank=True, default=0)
    # cryptos_usd = models.FloatField(null=True, blank=True, default=0)
    # percentual_cryptos = models.CharField(max_length=10, null=True, blank=True, default='')
    # etfs_br = models.FloatField(null=True, blank=True, default=0)
    # percentual_etfs_br = models.CharField(max_length=10, null=True, blank=True, default='')
    # etfs_us = models.FloatField(null=True, blank=True, default=0)
    # percentual_etfs_us = models.CharField(max_length=10, null=True, blank=True, default='')
    # dividendos_reinvestidos = models.FloatField(null=True, blank=True)

    objects = QuerySet.as_manager()


class Registro(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    created = models.DateTimeField(default=timezone.now, blank=True)
    # tudo referente à moeda de saída
    moeda_utilizada = models.CharField(max_length=10)
    custo_total = models.DecimalField(max_digits=14, decimal_places=6, default=0.00)
    total_saida_brl = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    cotacao_sai_brl = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    total_saida_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    cotacao_sai_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    # tudo referente à moeda de entrada
    ativo_adquirido = models.CharField(max_length=10)
    qtd_entrada = models.DecimalField(max_digits=14, decimal_places=6, default=0.00)
    total_entrada_brl = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    cotacao_ent_brl = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    total_entrada_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)
    cotacao_ent_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True)

    taxa = models.DecimalField(max_digits=14, decimal_places=6, default=0, null=True)
    cambio_usd = models.FloatField(null=True, blank=True, default=0.00)
    de_dividendos = models.BooleanField(null=True, blank=True, default=False)

    objects = QuerySet.as_manager()
