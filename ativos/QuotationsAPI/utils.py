import datetime
import requests
from time import sleep
from django.db.models import Sum
import yfinance as yf


# YAHOO Finance
def quotation_brl(classe, nome):
    if classe in ['ações', 'fiis', 'etf_br']:
        ticker = yf.Ticker(nome+".SA")
        cotacao = ticker.history_metadata['regularMarketPrice']
        return round(cotacao, 2)

    if classe in ['stocks', 'reits', 'etfs_us']:
        ticker = yf.Ticker(nome)
        cotacao = ticker.history_metadata['regularMarketPrice']
        return round(to_brl(cotacao), 2)

    if classe == 'cryptos':
        ticker = yf.Ticker(nome+"-USD")
        cotacao = ticker.history_metadata['regularMarketPrice']
        rounded_cotacao = round(to_brl(cotacao), 6)
        formatted_cotacao = '{:.6f}'.format(rounded_cotacao).rstrip('0').rstrip('.')
        return formatted_cotacao


def quotation_usd(classe, nome):
    if classe in ['ações', 'fiis', 'etf_br']:
        ticker = yf.Ticker(nome + ".SA")
        cotacao = ticker.history_metadata['regularMarketPrice']
        return to_usd(round(cotacao, 2))
    if classe in ['stocks', 'reits', 'etfs_us']:
        ticker = yf.Ticker(nome)
        cotacao = ticker.history_metadata['regularMarketPrice']
        return round(cotacao, 2)
    if classe == 'cryptos':
        ticker = yf.Ticker(nome + "-USD")
        cotacao = ticker.history_metadata['regularMarketPrice']
        rounded_cotacao = round(cotacao, 6)
        formatted_cotacao = '{:.6f}'.format(rounded_cotacao).rstrip('0').rstrip('.')
        return formatted_cotacao


USD = yf.Ticker("USDBRL=X").history_metadata['regularMarketPrice']


def to_usd(valor, request_usd=None):
    usd = yf.Ticker("USDBRL=X").history_metadata['regularMarketPrice']
    if request_usd:
        usd = request_usd
    valor_usd = round(valor / usd, 2)
    return valor_usd


def to_brl(valor, request_usd=None):
    usd = yf.Ticker("USDBRL=X").history_metadata['regularMarketPrice']
    if request_usd:
        usd = request_usd
    valor_brl = round(valor * usd, 2)
    return valor_brl


def updated_full_patrimony_value(atv):
    try:
        nomes = list(atv.values_list('nome', flat=True).values())
        valor_total_ativo_tempo_real = []
        cotacao = 0
        for n in nomes:
            quantidade = n['quantidade']
            cotacao = quotation_AC_FII(f"{n['nome']}.SAO") if n['classe'] in ['ações', 'fiis', 'etfs_br'] \
                else cotacao == quotation_AC_FII(f"{n['nome']}")
            valor_total_ativo_tempo_real.append(quantidade * cotacao)
        return sum(valor_total_ativo_tempo_real)
    except:
        return 0


def updated_full_acoes_value(atv):
    try:
        nomes = list(atv.filter(classe='ações').values())
        valor_acoes_tempo_real = []
        for n in nomes:
            quantidade = n['quantidade']
            cotacao = quotation_AC_FII(f"{n['nome']}.SAO")
            valor_acoes_tempo_real.append(quantidade * cotacao)
        return sum(valor_acoes_tempo_real)
    except:
        return 0


# Every time an operation is done, all percentages and market value should be updated with current value
def update_assets_values(usd):
    from ativos.models import Ativo  # Importing inside the function to avoid circular import

    for ativo in Ativo.objects.all():
        if ativo.classe != 'caixa':
            other_un_atual_brl = quotation_brl(ativo.classe, ativo.nome)
            other_un_atual_usd = quotation_usd(ativo.classe, ativo.nome)
            other_total_atual = float(other_un_atual_brl) * float(ativo.quantidade)
            other_total_atual_usd = float(other_un_atual_usd) * float(ativo.quantidade)
            other_lucro_preju = other_total_atual - float(ativo.pm_un) * float(ativo.quantidade)
            other_lucro_preju_usd = to_usd(other_lucro_preju)
            other_perc_lucro = float(other_lucro_preju) * 100 / float(ativo.custo_total)
            other_perc_grupo = other_perc_total = None
            sum_total_atual = Ativo.objects.filter(classe=ativo.classe).aggregate(Sum('total_atual'))[
                'total_atual__sum']
            if sum_total_atual is not None:
                other_perc_grupo = float(ativo.total_atual) / float(sum_total_atual)

            sum_total_atual = \
                Ativo.objects.filter(presente=True).aggregate(Sum('total_atual'))['total_atual__sum']
            if sum_total_atual is not None:
                other_perc_total = float(ativo.total_atual) / float(sum_total_atual)

            Ativo.objects.filter(id=ativo.id).update(
                perc_grupo=other_perc_grupo,
                perc_total=other_perc_total,
                un_atual_brl=other_un_atual_brl,
                un_atual_usd=other_un_atual_usd,
                total_atual=other_total_atual,
                total_atual_usd=other_total_atual_usd,
                lucro_preju=other_lucro_preju,
                lucro_preju_usd=other_lucro_preju_usd,
                perc_lucro=other_perc_lucro
            )
        else:
            un_atual_usd = float(usd)
            total_atual_usd = float(ativo.total_atual) / float(usd)
            lucro_preju_usd = to_usd(float(ativo.lucro_preju))
            perc_lucro = float(ativo.lucro_preju) * 100 / float(ativo.custo_total)
            perc_grupo = perc_total = None
            sum_total_atual_class = Ativo.objects.filter(classe=ativo.classe).aggregate(Sum('total_atual'))[
                'total_atual__sum']
            if sum_total_atual_class is not None:
                perc_grupo = float(ativo.total_atual) / float(sum_total_atual_class)
            sum_total_atual = Ativo.objects.filter(presente=True).aggregate(Sum('total_atual'))[
                'total_atual__sum']
            if sum_total_atual is not None:
                perc_total = float(ativo.total_atual) / float(sum_total_atual)

            Ativo.objects.filter(id=ativo.id).update(
                un_atual_usd=un_atual_usd,
                perc_grupo=perc_grupo,
                perc_total=perc_total,
                total_atual_usd=total_atual_usd,
                lucro_preju=ativo.lucro_preju,
                lucro_preju_usd=lucro_preju_usd,
                perc_lucro=perc_lucro
            )


def selling_used_coin_to_buy_assets(used_coin, asset_class, sold_quantity):
    from ativos.models import Ativo  # Importing inside the function to avoid circular import

    # assets table update
    sold_asset = Ativo.objects.get(nome=used_coin)
    quantidade = float(sold_asset.quantidade) - sold_quantity

    new_avg_cost = (float(sold_asset.pm_un) * float(sold_asset.quantidade) -
                    float(quotation_brl(asset_class, used_coin)) * float(sold_quantity)) / (float(sold_asset.quantidade)
                                                                                            - float(sold_quantity))

    # Updating Sold Asset in DB
    sold_asset.quantidade = quantidade
    sold_asset.pm_un = new_avg_cost
    sold_asset.modified = datetime.datetime.now()
    sold_asset.save()

    # Transactions records and Patrimony update are not needed. It's done by the POST Request Standard.
