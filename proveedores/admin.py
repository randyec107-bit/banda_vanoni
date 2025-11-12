from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "tipo_proveedor", "tipo_identificacion", "numero_identificacion", "pais", "ciudad")
    search_fields = ("razon_social", "numero_identificacion", "pais")
    list_filter = ("tipo_proveedor", "pais", "tipo_identificacion")
    readonly_fields = ("ciudad",)  
