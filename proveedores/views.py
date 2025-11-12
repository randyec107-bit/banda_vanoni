# proveedores/views.py
from django.http import HttpResponse

def proveedores_home(request):
    return HttpResponse("✅ Módulo Proveedores funcionando")
