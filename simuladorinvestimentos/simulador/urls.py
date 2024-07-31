from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/getdata', views.get_data, name='get_data'),
    path('api/nova_simulacao_automatica', views.nova_simulacao_automatica, name='nova_simulacao_automatica'),
    path('api/pesquisar_ativos/', views.pesquisar_ativos, name='pesquisar_ativos'),
]
