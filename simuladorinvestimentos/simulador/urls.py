from django.urls import path
from . import views

urlpatterns = [
    path('nova_simulacao_automatica/', views.nova_simulacao_automatica, name='nova_simulacao_automatica'),
    path('pesquisar_ativos/', views.pesquisar_ativos, name='pesquisar_ativos'),
    path('enviar_ativos/', views.enviar_ativos, name='enviar_ativos'),
    path('historico/', views.listar_historico, name='listar_historico'),
    path('excluir_simulacao_automatica/<int:simulacao_id>/', views.excluir_simulacao_automatica, name='excluir_simulacao_automatica'),
    path('excluir_simulacao_manual/<int:simulacao_id>/', views.excluir_simulacao_manual, name='excluir_simulacao_manual'),
    path('resultado_simulacao_automatica/', views.resultado_simulacao_automatica, name='resultado_simulacao_automatica'),
    path('abrir_simulacao_automatica/', views.abrir_simulacao_automatica, name='abrir_simulacao_automatica'),

    path('nova_simulacao_manual/', views.nova_simulacao_manual, name='nova_simulacao_manual'),
    path('simulacao_manual/<int:simulacao_id>/', views.simulacao_manual, name='simulacao_manual'),
    path('modificar_dinheiro/<int:simulacao_id>/', views.modificar_dinheiro_view, name='modificar_dinheiro'),
    path('avancar_mes/<int:simulacao_id>/', views.avancar_mes_view, name='avancar_mes'),
    path('negociar_ativos_pesquisa/<int:simulacao_id>/', views.negociar_ativos_pesquisa, name='negociar_ativos_pesquisa'),
    path('negociar_ativos/<int:simulacao_id>/', views.negociar_ativos, name='negociar_ativos'),
    path('buy_sell_actives/<int:simulacao_id>/', views.buy_sell_actives, name='buy_sell_actives'),
]

