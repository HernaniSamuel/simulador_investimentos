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
    path('getdata/', views.get_data, name='get_data'), # será a pesquisa e análise de ativos da simulação manual
]
