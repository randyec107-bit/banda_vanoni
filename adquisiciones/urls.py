# adquisiciones/urls.py
from django.urls import path
from . import views
from .views import adquisiciones_home
from .views import exportar_adquisiciones_excel

urlpatterns = [
    path('adquisiciones/', adquisiciones_home, name='adquisiciones_home'),
    path("exportar_excel/", exportar_adquisiciones_excel, name="exportar_excel"),
    path('adquisiciones/<int:adquisicion_id>/', views.detalle_adquisicion, name='detalle_adquisicion'),
]
