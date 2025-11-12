from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_principal, name='dashboard_principal'),
    
]