from django.urls import path
from . import views

urlpatterns = [
    path('getdata/', views.get_data, name='get_data'),
    path('nova_simulacao_automatica/', views.nova_simulacao_automatica, name='nova_simulacao_automatica'),
    path('pesquisar_ativos/', views.pesquisar_ativos, name='pesquisar_ativos'),
    path('enviar_ativos/', views.enviar_ativos, name='enviar_ativos'),
    path('historico/', views.listar_historico, name='listar_historico'),
    path('excluir_simulacao/<int:simulacao_id>/', views.excluir_simulacao, name='excluir_simulacao'),
    path('resultado_simulacao_automatica/', views.resultado_simulacao_automatica, name='resultado_simulacao_automatica'),
    path('abrir_simulacao_automatica/', views.abrir_simulacao_automatica, name='abrir_simulacao_automatica'),
]
