from rest_framework import serializers
from .models import Ativo, Patrimonio, Registro


class AtivoPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ativo
        fields = ('classe', 'nome', 'total_atual', 'quantidade', 'custo_total', 'max_pago', 'min_pago',
                  )


class AtivoGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ativo
        fields = '__all__'


class PatrimonioGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrimonio
        fields = ['created', 'patrimonio', 'patrimonio_usd', 'classes_percent', 'classes_values', 'assets_percent',
                  'assets_values']


class RegistroGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registro
        fields = ['created', 'moeda_utilizada', 'custo_total', 'ativo_adquirido', 'qtd_entrada', 'cotacao_ent_brl',
                  'cotacao_ent_usd', 'taxa', 'cambio_usd']


class CashGetPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ativo
        fields = ['modified', 'classe', 'total_atual', 'total_atual_usd']
