# productos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.productos_home, name="productos_home"),
]
