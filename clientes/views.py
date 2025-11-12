# clientes/views.py
from django.http import HttpResponse

def lista_clientes(request):
    return HttpResponse("✅ Módulo Clientes funcionando")
