from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/getdata', views.get_data, name='get_data'),
]
