from django.urls import path
from . import views

urlpatterns = [
    path('getdata/', views.get_data, name='get_data'),
    path('nova_simulacao_automatica/', views.nova_simulacao_automatica, name='nova_simulacao_automatica'),
    path('pesquisar_ativos/', views.pesquisar_ativos, name='pesquisar_ativos'),
    path('enviar_ativos/', views.enviar_ativos, name='enviar_ativos'),
]
