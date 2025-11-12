# proveedores/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.proveedores_home, name='proveedores_home'),
]
