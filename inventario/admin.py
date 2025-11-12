from django.contrib import admin
from .models import InventarioProducto, AlmacenProducto
from productos.models import ProductoLote



@admin.register(InventarioProducto)
class InventarioProductoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre',
        'registro_sanitario',
        'ubicacion',
        'precio1',
        'precio2',
        'precio3',
        'fecha_elaboracion',
        'vigencia_lote',
        'cantidad_total',
    )
    search_fields = ('codigo', 'nombre', 'registro_sanitario', 'proveedor_principal')
    list_filter = ('ubicacion', 'activo', 'grupo__descripcion', 'subgrupo__descripcion', 'clasificacion__descripcion')
    ordering = ('nombre',)
    list_per_page = 30

    @admin.display(description="Fecha de Elaboración")
    def fecha_elaboracion(self, obj):
        return obj.fecha_elaboracion

    @admin.display(description="Vigencia del Lote")
    def vigencia_lote(self, obj):
        return obj.vigencia_lote

    @admin.display(description="Cantidad Total")
    def cantidad_total(self, obj):
        return obj.cantidad_total



@admin.register(AlmacenProducto)
class AlmacenProductoAdmin(admin.ModelAdmin):
    list_display = (
        'get_codigo',
        'get_nombre',
        'get_bodega_display',
        'seccion',
        'estante',
        'get_ubicacion',
        'get_activo',
    )
    search_fields = (
        'producto__codigo',
        'producto__nombre',
        'bodega',
        'producto__ubicacion',
    )
    list_filter = ('bodega', 'producto__ubicacion', 'producto__activo')
    ordering = ('producto__nombre',)
    list_per_page = 30

    
    @admin.display(description="Código")
    def get_codigo(self, obj):
        return obj.codigo

    @admin.display(description="Nombre")
    def get_nombre(self, obj):
        return obj.nombre

    @admin.display(description="Bodega / Ubicación")
    def get_bodega_display(self, obj):
        """
        Si la bodega está vacía, usa la ubicación del producto.
        """
        return obj.bodega or obj.producto.ubicacion or "Sin ubicación"

    @admin.display(description="Ubicación del Producto")
    def get_ubicacion(self, obj):
        return obj.producto.ubicacion or "Sin ubicación"

    @admin.display(description="Activo")
    def get_activo(self, obj):
        return "✅" if obj.producto.activo else "❌"
