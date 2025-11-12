# urls.py de pedidos
from . import views
from django.urls import path

urlpatterns = [
    
    path('factura/<int:pk>/pdf/', views.factura_pdf, name='factura_pdf'),
]

