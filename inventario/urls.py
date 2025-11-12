# inventario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventario_home, name='inventario_home'),
]
