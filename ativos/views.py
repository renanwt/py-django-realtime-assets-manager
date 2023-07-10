import rest_framework.status
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .QuotationsAPI.utils import to_usd, to_brl, quotation_brl, quotation_usd, USD, update_assets_values, \
    selling_used_coin_to_buy_assets
from .models import Ativo, Registro, Patrimonio
from .serializers import AtivoPostSerializer, AtivoGetSerializer, PatrimonioGetSerializer, RegistroGetSerializer, \
    CashGetPostSerializer
from django.db.models import Sum


class GetPostAtivo(GenericAPIView):
    serializer_class = AtivoPostSerializer
    queryset = Ativo.objects.all()

    def get(self, request, *args, **kwargs):
        classe = kwargs.get('classe', '').lower()
        valid_classes = ['ações', 'fiis', 'stocks', 'reits', 'cryptos', 'etfs_br', 'etfs_us']

        if classe not in valid_classes and classe != '':
            return Response("Class not identified. Please try these lower case classes: 'ações', 'fiis', 'stocks', "
                            "'reits', 'cryptos', 'etfs_br' or 'etfs_us' ",
                            status=rest_framework.status.HTTP_404_NOT_FOUND)

        ativos = self.queryset.all()
        if classe:
            ativos = self.queryset.filter(classe=classe)

        serializer = AtivoGetSerializer(ativos, many=True)
        return Response(serializer.data, status=rest_framework.status.HTTP_200_OK)

    def post(self, request, **kwargs):
        try:
            moeda_utilizada = request.data.get('moeda_utilizada', None)
            quantidade_sai = request.data.get('quantidade_sai', None)
            usd = request.data.get('usd', USD)
            classe = kwargs['classe'].lower()
            nome = request.data['nome']
            qtd_comprada = request.data['quantidade']
            preco = request.data['preço_un']
            if classe in ['cryptos', 'stocks', 'reits', 'etfs_us']:
                preco = to_brl(preco, usd)
            dividendos = request.data.get('dividendos', False)
            created = request.data.get('created', timezone.now())
            modified = request.data.get('modified', timezone.now())
            taxas = request.data.get('taxas', 0)

        except Exception as e:
            return Response("Failed to collect request body data: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                # Checking existing used_coin (for cryptos)
                if moeda_utilizada and quantidade_sai is not None:
                    selling_used_coin_to_buy_assets(moeda_utilizada, classe, quantidade_sai)

                # ASSET Creation
                if not Ativo.objects.all().filter(nome=nome):
                    ativo = Ativo.objects.create(
                        classe=classe,
                        nome=nome,
                        quantidade=qtd_comprada,
                        created=created,
                        pm_un=preco,
                        min_pago=preco,
                        max_pago=preco
                    )
                else:
                    ativo = Ativo.objects.get(nome=nome)
                    quantidade = float(ativo.quantidade) + qtd_comprada
                    pm_novo = (float(preco) * float(qtd_comprada) + float(ativo.pm_un) * float(ativo.quantidade)) / \
                              (float(ativo.quantidade) + float(qtd_comprada))

                    min_pago_novo = ativo.min_pago
                    max_pago_novo = ativo.max_pago
                    if preco < ativo.min_pago:
                        min_pago_novo = preco
                    elif preco > ativo.max_pago:
                        max_pago_novo = preco
                    else:
                        min_pago_novo = ativo.min_pago
                        max_pago_novo = ativo.max_pago

                    # ASSET Update
                    ativo.quantidade = quantidade
                    ativo.pm_un = pm_novo
                    ativo.min_pago = min_pago_novo
                    ativo.max_pago = max_pago_novo
                    ativo.modified = modified
                    ativo.save()

                # Updating floating data for all rows in the table (generic for caixa and ativos)
                update_assets_values(usd)

            except Exception as e:
                transaction.set_rollback(True)
                return Response("Failed to save asset: " + str(e), status=status.HTTP_400_BAD_REQUEST)

            try:
                moeda_utilizada = total_saida_brl = cotacao_sai_brl = total_saida_usd = cotacao_sai_usd = None
                total_entrada_brl = cotacao_ent_brl = total_entrada_usd = cotacao_ent_usd = custo_total = None

                # RECORDS Table interactions
                if classe in ['ações', 'fiis', 'etfs_br']:
                    moeda_utilizada = 'BRL'
                    custo_total = preco * qtd_comprada
                    cotacao_ent_brl = preco
                    cotacao_ent_usd = preco / usd
                    cotacao_sai_usd = None
                    total_saida_brl = cotacao_sai_brl = total_saida_usd = None
                    total_entrada_brl = total_entrada_usd = None

                elif classe in ['stocks', 'reits', 'etfs_us']:
                    moeda_utilizada = 'USD'
                    custo_total = request.data['preço_un'] * qtd_comprada
                    total_saida_brl = preco * qtd_comprada
                    cotacao_sai_brl = cotacao_sai_usd = total_saida_usd = None
                    cotacao_ent_usd = request.data['preço_un']
                    cotacao_ent_brl = preco
                    total_entrada_usd = total_entrada_brl = None

                elif classe == 'cryptos':
                    moeda_utilizada = request.data['moeda_utilizada']
                    if moeda_utilizada not in ['BRL', 'USD']:
                        custo_total = request.data['quantidade_sai']  # custo na moeda utilizada
                    ativo_adquirido = request.data['nome']

                    if moeda_utilizada == 'BRL':
                        total_saida_brl = preco * qtd_comprada
                        cotacao_sai_brl = 1
                        total_saida_usd = to_usd(preco, usd)
                        cotacao_sai_usd = to_usd(cotacao_sai_brl, usd)
                        custo_total = round(total_saida_brl, 2)  # custo na moeda utilizada
                    elif moeda_utilizada == 'USD':
                        total_saida_usd = preco
                        cotacao_sai_usd = 1
                        total_saida_brl = to_brl(preco, usd)
                        cotacao_sai_brl = to_brl(cotacao_sai_usd, usd)
                        custo_total = round(total_saida_usd, 2)  # custo na moeda utilizada
                    else:
                        out_currency = to_brl(request.data.get("preco_saida", quotation_brl(classe, moeda_utilizada)))
                        cotacao_sai_brl = out_currency
                        total_saida_brl = float(cotacao_sai_brl) * custo_total
                        cotacao_sai_usd = to_usd(out_currency, usd)
                        total_saida_usd = float(cotacao_sai_usd) * custo_total

                    if ativo_adquirido == 'BRL':
                        cotacao_ent_brl = 1
                        total_entrada_brl = cotacao_ent_brl * qtd_comprada
                        cotacao_ent_usd = to_usd(cotacao_ent_brl, usd)
                        total_entrada_usd = to_usd(total_entrada_brl, usd)
                    else:
                        cotacao_ent_brl = preco
                        total_entrada_brl = cotacao_ent_brl * qtd_comprada
                        cotacao_ent_usd = request.data['preço_un']
                        total_entrada_usd = cotacao_ent_usd * qtd_comprada
                Registro.objects.create(
                    moeda_utilizada=moeda_utilizada,
                    custo_total=custo_total,
                    total_saida_brl=total_saida_brl,
                    cotacao_sai_brl=cotacao_sai_brl,
                    total_saida_usd=total_saida_usd,
                    cotacao_sai_usd=cotacao_sai_usd,
                    ativo_adquirido=nome,
                    qtd_entrada=qtd_comprada,
                    total_entrada_brl=total_entrada_brl,
                    cotacao_ent_brl=cotacao_ent_brl,
                    total_entrada_usd=total_entrada_usd,
                    cotacao_ent_usd=cotacao_ent_usd,
                    taxa=taxas,
                    cambio_usd=USD,
                    de_dividendos=dividendos,
                    created=created
                )
            except Exception as e:
                transaction.set_rollback(True)
                return Response("Failed to insert records: " + str(e), status=status.HTTP_400_BAD_REQUEST)

            # PATRIMONY Table update
            try:
                class_totals = {}
                class_list = ["ações", "fiis", "stocks", "reits", "cryptos", "caixa"]

                for classe in class_list:
                    try:
                        total_classe = float(
                            Ativo.objects.filter(classe=classe).aggregate(Sum('total_atual'))['total_atual__sum'])
                        class_totals[classe] = total_classe
                    except TypeError:
                        class_totals[classe] = 0.0

                # Calculate the percentage for each class
                total_patrimonio = sum(class_totals.values())
                patrimonio_usd = to_usd(total_patrimonio)

                classes_percent = {}
                for classe in class_totals:
                    if total_patrimonio:
                        classes_percent[classe] = str(
                            round(float(class_totals[classe] / total_patrimonio) * 100, 2)) + " %"
                    else:
                        classes_percent[classe] = "0.00 %"

                assets_percent = {}
                assets_values = {}
                ativos = Ativo.objects.all()

                for ativo in ativos:
                    nome = ativo.nome
                    percent = ativo.perc_total
                    total_atual = ativo.total_atual
                    if nome not in assets_percent:
                        assets_percent[nome] = str(round(float(percent) * 100, 2)) + " %"
                    else:
                        assets_percent[nome] += str(round(float(percent) * 100, 2)) + " %"
                    if nome not in assets_values:
                        assets_values[nome] = "R$ " + str(float(total_atual))
                    else:
                        assets_values[nome] += "R$ " + str(float(total_atual))

                # PATRIMONY update
                patrimonio = Patrimonio.objects.create(
                    patrimonio=total_patrimonio,
                    patrimonio_usd=patrimonio_usd,
                    classes_percent=classes_percent,
                    classes_values={
                        "ações": "R$ " + str(float(class_totals.get("ações", 0.0))),
                        "fiis": "R$ " + str(float(class_totals.get("fiis", 0.0))),
                        "cryptos": "R$ " + str(float(to_brl(class_totals.get("cryptos", 0.0)))),
                        "stocks": "R$ " + str(float(to_brl(class_totals.get("stocks", 0.0)))),
                        "reits": "R$ " + str(float(to_brl(class_totals.get("reits", 0.0))))
                    },
                    assets_percent=assets_percent,
                    assets_values=assets_values
                )
            except Exception as e:
                transaction.set_rollback(True)
                return Response("Failed updating Patrimony: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        serializer = AtivoPostSerializer(data=ativo.__dict__)
        if serializer.is_valid():
            ativo.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class GetPatrimony(GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            patrimonio = Patrimonio.objects.last()
            serializer = PatrimonioGetSerializer(patrimonio)
            return Response(serializer.data, status=rest_framework.status.HTTP_200_OK)
        except Exception as e:
            return Response("Failure getting Patrimony data: " + str(e), status=status.HTTP_400_BAD_REQUEST)


class GetRegister(GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            registro = Registro.objects.all()
            serializer = RegistroGetSerializer(registro, many=True)
            return Response(serializer.data, status=rest_framework.status.HTTP_200_OK)
        except Exception as e:
            return Response("Failure getting Register data: " + str(e), status=status.HTTP_400_BAD_REQUEST)


class GetPostCaixa(GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            caixa = Ativo.objects.get(classe='caixa')
            serializer = RegistroGetSerializer(caixa, many=True)
            return Response(serializer.data, status=rest_framework.status.HTTP_200_OK)
        except Exception as e:
            return Response("Failure getting cash data: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            nome = request.data['nome']
            lucro_preju = request.data.get('juros', 0)
            preco = request.data['aporte']
            usd = request.data.get('usd', USD)
            dividendos = request.data.get('dividendos', False)
            created = request.data.get('created', timezone.now())
            modified = request.data.get('modified', timezone.now())
        except Exception as e:
            return Response("Failed to collect request body data: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                if not Ativo.objects.filter(nome=nome).exists():
                    # Creating a new row in the table for CAIXA
                    ativo = Ativo.objects.create(
                        classe='caixa',
                        nome=nome,
                        quantidade=1.0,
                        created=created,
                        pm_un=preco,
                        min_pago=preco,
                        max_pago=preco,
                        custo_total=preco,
                        total_atual=preco + lucro_preju,
                        lucro_preju=lucro_preju
                    )
                else:
                    ativo = Ativo.objects.get(nome=nome)
                    custo_total_novo = float(ativo.custo_total) - float(ativo.lucro_preju) + float(preco) + \
                                       float(lucro_preju)
                    total_atual = float(ativo.custo_total) + float(preco) + float(lucro_preju)
                    quantidade = float(ativo.quantidade) + float(1)
                    pm_novo = (float(preco) * float(1) + float(ativo.pm_un) * float(ativo.quantidade)) / \
                              (float(ativo.quantidade) + float(1))

                    min_pago_novo = ativo.min_pago
                    max_pago_novo = ativo.max_pago
                    if preco < ativo.min_pago:
                        min_pago_novo = preco
                    elif preco > ativo.max_pago:
                        max_pago_novo = preco
                    else:
                        min_pago_novo = ativo.min_pago
                        max_pago_novo = ativo.max_pago

                    # Updating the existing row in the table for CAIXA
                    ativo.quantidade = quantidade
                    ativo.pm_un = pm_novo
                    ativo.custo_total = custo_total_novo
                    ativo.total_atual = total_atual
                    ativo.lucro_preju = lucro_preju
                    ativo.min_pago = min_pago_novo
                    ativo.max_pago = max_pago_novo
                    ativo.modified = modified
                    ativo.save()

                # Updating floating data for all rows in the table (generic for caixa and ativos)
                update_assets_values(usd)

        except Exception as e:
            return Response("Failure saving cash / updating assets: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        try:
            ativo_adquirido = None
            if nome == 'BRL':
                ativo_adquirido = 'Caixa-BRL'
            elif nome == 'USD':
                ativo_adquirido = 'Caixa-USD'
            moeda_utilizada = 'BRL'
            total_saida_brl = 0.0
            cotacao_sai_brl = 1
            total_saida_usd = 0.0
            cotacao_sai_usd = usd
            total_entrada_brl = preco
            cotacao_ent_brl = 1
            total_entrada_usd = to_usd(preco)
            cotacao_ent_usd = usd
            custo_total = preco
            taxas = None
            qtd_comprada = 1

            Registro.objects.create(
                moeda_utilizada=moeda_utilizada,
                custo_total=custo_total,
                total_saida_brl=total_saida_brl,
                cotacao_sai_brl=cotacao_sai_brl,
                total_saida_usd=total_saida_usd,
                cotacao_sai_usd=cotacao_sai_usd,
                ativo_adquirido=ativo_adquirido,
                qtd_entrada=qtd_comprada,
                total_entrada_brl=total_entrada_brl,
                cotacao_ent_brl=cotacao_ent_brl,
                total_entrada_usd=total_entrada_usd,
                cotacao_ent_usd=cotacao_ent_usd,
                taxa=taxas,
                cambio_usd=USD,
                de_dividendos=dividendos,
                created=created
            )
        except Exception as e:
            return Response("Fail to insert into register: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        # TODO: formula pro Patrimonio

        try:
            # atualização do PATRIMONIO
            class_totals = {}
            class_list = ["ações", "fiis", "stocks", "reits", "cryptos", "caixa"]

            for classe in class_list:
                try:
                    total_classe = float(
                        Ativo.objects.filter(classe=classe).aggregate(Sum('total_atual'))['total_atual__sum'])
                    class_totals[classe] = total_classe
                except TypeError:
                    class_totals[classe] = 0.0

            # Calculate the percentage for each class
            total_patrimonio = sum(class_totals.values())
            patrimonio_usd = to_usd(total_patrimonio)

            classes_percent = {}
            for classe in class_totals:
                classes_percent[classe] = str(round(float(class_totals[classe] / total_patrimonio) * 100, 2)) + " %"

            assets_percent = {}
            assets_values = {}
            ativos = Ativo.objects.all()

            for ativo in ativos:
                nome = ativo.nome
                percent = ativo.perc_total
                total_atual = ativo.total_atual
                if nome not in assets_percent:
                    assets_percent[nome] = str(round(float(percent) * 100, 2)) + " %"
                else:
                    assets_percent[nome] += str(round(float(percent) * 100, 2)) + " %"
                if nome not in assets_values:
                    assets_values[nome] = "R$ " + str(float(total_atual))
                else:
                    assets_values[nome] += "R$ " + str(float(total_atual))

            # Create the patrimonio object with the calculated values
            patrimonio = Patrimonio.objects.create(
                patrimonio=total_patrimonio,
                patrimonio_usd=patrimonio_usd,
                classes_percent=classes_percent,
                classes_values={
                    "ações": "R$ " + str(float(class_totals.get("ações", 0.0))),
                    "fiis": "R$ " + str(float(class_totals.get("fiis", 0.0))),
                    "crypto": "R$ " + str(float(to_brl(class_totals.get("crypto", 0.0)))),
                    "stocks": "R$ " + str(float(to_brl(class_totals.get("stocks", 0.0)))),
                    "reits": "R$ " + str(float(to_brl(class_totals.get("reits", 0.0)))),
                    "caixa": "R$ " + str(float(class_totals.get("caixa", 0.0))),
                },
                assets_percent=assets_percent,
                assets_values=assets_values
            )
        except Exception as e:
            return Response("Failure updating Patrimony: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        serializer = CashGetPostSerializer(data=ativo.__dict__)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class DeleteAsset(GenericAPIView):
    def delete(self, request, **kwargs):
        with transaction.atomic():
            try:
                asset_name = kwargs['asset_name'].upper()
                usd = float(request.query_params.get('usd', USD))
            except Exception as e:
                return Response("Failed to collect request body data: " + str(e), status=status.HTTP_400_BAD_REQUEST)

            # Getting Asset Details:
            try:
                asset = Ativo.objects.get(nome=asset_name)
                asset_class = asset.classe
                asset_quantity = asset.quantidade
                cotacao_sai_brl = float(quotation_brl(asset_class, asset_name))
                total_saida_brl = float(asset_quantity) * float(cotacao_sai_brl)
                cotacao_sai_usd = to_usd(cotacao_sai_brl)
                total_saida_usd = to_usd(total_saida_brl)
            except Exception as e:
                return Response("Asset data not collected: " + str(e), status=status.HTTP_404_NOT_FOUND)


            # RECORDS Table interaction
            try:
                Registro.objects.create(
                    moeda_utilizada=asset_name,
                    custo_total=asset_quantity,   #total utilizado
                    total_saida_brl=total_saida_brl,
                    cotacao_sai_brl=cotacao_sai_brl,
                    total_saida_usd=total_saida_usd,
                    cotacao_sai_usd=cotacao_sai_usd,
                    ativo_adquirido='BRL',
                    qtd_entrada=0.0,
                    total_entrada_brl=0.0,
                    cotacao_ent_brl=0.0,
                    total_entrada_usd=0.0,
                    cotacao_ent_usd=0.0,
                    taxa=0.0,
                    cambio_usd=USD,
                    de_dividendos=bool(False),
                    created=timezone.now()
                )
            except Exception as e:
                return Response("Failed to insert records: " + str(e), status=status.HTTP_400_BAD_REQUEST)

            # ASSETS Table interaction
            try:
                asset.delete()
                update_assets_values(usd)  # Update asset values after deletion

            except Exception as e:
                transaction.set_rollback(True)
                return Response("Failed to delete Asset: " + str(e), status=status.HTTP_400_BAD_REQUEST)

            # PATRIMONY interaction
            try:
                class_totals = {}
                class_list = ["ações", "fiis", "stocks", "reits", "cryptos", "caixa"]

                for classe in class_list:
                    try:
                        total_classe = float(
                            Ativo.objects.filter(classe=classe).aggregate(Sum('total_atual'))['total_atual__sum'])
                        class_totals[classe] = total_classe
                    except TypeError:
                        class_totals[classe] = 0.0

                # Calculate the percentage for each class
                total_patrimonio = sum(class_totals.values())
                patrimonio_usd = to_usd(total_patrimonio)

                classes_percent = {}
                for classe in class_totals:
                    if total_patrimonio:
                        classes_percent[classe] = str(
                            round(float(class_totals[classe] / total_patrimonio) * 100, 2)) + " %"
                    else:
                        classes_percent[classe] = "0.00 %"

                assets_percent = {}
                assets_values = {}
                ativos = Ativo.objects.all()

                for ativo in ativos:
                    nome = ativo.nome
                    percent = ativo.perc_total
                    total_atual = ativo.total_atual
                    if nome not in assets_percent:
                        assets_percent[nome] = str(round(float(percent) * 100, 2)) + " %"
                    else:
                        assets_percent[nome] += str(round(float(percent) * 100, 2)) + " %"
                    if nome not in assets_values:
                        assets_values[nome] = "R$ " + str(float(total_atual))
                    else:
                        assets_values[nome] += "R$ " + str(float(total_atual))

                # PATRIMONY update
                patrimonio = Patrimonio.objects.create(
                    patrimonio=total_patrimonio,
                    patrimonio_usd=patrimonio_usd,
                    classes_percent=classes_percent,
                    classes_values={
                        "ações": "R$ " + str(float(class_totals.get("ações", 0.0))),
                        "fiis": "R$ " + str(float(class_totals.get("fiis", 0.0))),
                        "cryptos": "R$ " + str(float(to_brl(class_totals.get("cryptos", 0.0)))),
                        "stocks": "R$ " + str(float(to_brl(class_totals.get("stocks", 0.0)))),
                        "reits": "R$ " + str(float(to_brl(class_totals.get("reits", 0.0))))
                    },
                    assets_percent=assets_percent,
                    assets_values=assets_values
                )
                return Response("Asset deleted successfully.", status=status.HTTP_200_OK)
            except Exception as e:
                transaction.set_rollback(True)
                return Response("Failed updating Patrimony: " + str(e), status=status.HTTP_400_BAD_REQUEST)


