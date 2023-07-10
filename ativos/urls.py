from django.urls import path
from . import views

urlpatterns = [
    path('', views.GetPostAtivo.as_view(), name='Lista-de-Todos-Ativos'),
    path('caixa', views.GetPostCaixa.as_view(), name='Registro-de-Caixa'),
    path('classe/<str:classe>', views.GetPostAtivo.as_view(), name='Lista-de-Determinada-Classe-de-Ativo'),
    path('patrimony/', views.GetPatrimony.as_view(), name='Patrimonio-Total'),
    path('register/', views.GetRegister.as_view(), name='Registros-Total'),
    path('delete/<str:asset_name>', views.DeleteAsset.as_view(), name='Delete-Asset'),
    #path('sell/<str:classe>', views.SellAtivo.as_view(), name='Lista-de-Determinada-Classe-de-Ativo')
]
