from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GrupoProducto,
    SubgrupoProducto,
    ClasificacionProducto,
    Producto,
    ProductoLote,
)



@admin.register(GrupoProducto)
class GrupoProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "get_descripcion_display", "proveedor")
    search_fields = ("codigo", "descripcion", "proveedor")
    ordering = ("codigo",)
    list_per_page = 25

    def get_descripcion_display(self, obj):
        return obj.get_descripcion_display()
    get_descripcion_display.short_description = "Descripción"


@admin.register(SubgrupoProducto)
class SubgrupoProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "get_descripcion_display", "grupo", "proveedor")
    search_fields = ("codigo", "descripcion", "grupo__descripcion", "proveedor")
    list_filter = ("grupo__descripcion",)
    ordering = ("grupo__codigo", "codigo")
    list_per_page = 25

    def get_descripcion_display(self, obj):
        return obj.get_descripcion_display()
    get_descripcion_display.short_description = "Descripción"


@admin.register(ClasificacionProducto)
class ClasificacionProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "get_descripcion_display", "subgrupo", "proveedor")
    search_fields = ("codigo", "descripcion", "subgrupo__descripcion", "proveedor")
    list_filter = ("subgrupo__grupo__descripcion", "subgrupo__descripcion")
    ordering = ("subgrupo__grupo__codigo", "subgrupo__codigo", "codigo")
    list_per_page = 25

    def get_descripcion_display(self, obj):
        return obj.get_descripcion_display()
    get_descripcion_display.short_description = "Descripción"




class ProductoLoteInline(admin.TabularInline):
    model = ProductoLote
    extra = 1
    fields = ("lote", "fecha_elaboracion", "vigencia_lote", "cantidad", "stock_status")
    readonly_fields = ("stock_status",)
    show_change_link = True
    verbose_name = "Lote"
    verbose_name_plural = "Lotes de Producto"

    @admin.display(description="Estado Stock")
    def stock_status(self, obj):
        if obj.cantidad > 100:
            return format_html('<span style="color: green;">✅ Alto ({})</span>', obj.cantidad)
        elif obj.cantidad > 10:
            return format_html('<span style="color: orange;">⚠️ Medio ({})</span>', obj.cantidad)
        elif obj.cantidad > 0:
            return format_html('<span style="color: red;">🔴 Bajo ({})</span>', obj.cantidad)
        else:
            return format_html('<span style="color: gray;">❌ Agotado</span>')




@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "get_grupo_display",
        "get_subgrupo_display", 
        "get_clasificacion_display",
        "registro_sanitario",
        "ubicacion",
        "cantidad_total_display",  
        "precio1",
        "activo_display",  
    )

    search_fields = (
        "codigo",
        "nombre",
        "registro_sanitario",
        "proveedor_principal",
        "ean13",
        "ean14",
    )
    list_filter = (
        "grupo__descripcion",
        "subgrupo__descripcion", 
        "clasificacion__descripcion",
        "ubicacion",
        "activo",
    )
    readonly_fields = ("fecha_creacion", "fecha_actualizacion", "cantidad_total_display")
    inlines = [ProductoLoteInline]
    ordering = ("nombre",)
    list_per_page = 30
    list_select_related = ('grupo', 'subgrupo', 'clasificacion')  

    fieldsets = (
        ("Información General", {
            "fields": (
                "codigo", "nombre", "descripcion",
                "grupo", "subgrupo", "clasificacion",
                "proveedor_principal", "ubicacion", "activo"
            )
        }),
        ("Detalles Técnicos", {
            "fields": (
                "registro_sanitario", "vigencia_registro",
                "presentacion", "unidad_medida",
                "ean13", "ean14"
            )
        }),
        ("Precios y Stock", {
            "fields": ("precio1", "precio2", "precio3", "precio_especial", "stock_minimo", "cantidad_total_display")
        }),
        ("Tiempos del Sistema", {
            "classes": ("collapse",),
            "fields": ("fecha_creacion", "fecha_actualizacion"),
        }),
    )



    @admin.display(description="Stock Total")
    def cantidad_total_display(self, obj):
        """Suma todas las cantidades de los lotes asociados al producto."""
        try:
            total = sum(lote.cantidad for lote in obj.lotes.all())
            if total > 100:
                return format_html('<span style="color: green; font-weight: bold;">✅ {}</span>', total)
            elif total > 10:
                return format_html('<span style="color: orange; font-weight: bold;">⚠️ {}</span>', total)
            elif total > 0:
                return format_html('<span style="color: red; font-weight: bold;">🔴 {}</span>', total)
            else:
                return format_html('<span style="color: gray; font-weight: bold;">❌ {}</span>', total)
        except Exception:
            return format_html('<span style="color: gray;">0</span>')
    cantidad_total_display.admin_order_field = "lotes__cantidad"

    @admin.display(description="Activo")
    def activo_display(self, obj):
        return "✅ Sí" if obj.activo else "❌ No"
    activo_display.admin_order_field = "activo"

    def get_grupo_display(self, obj):
        return obj.grupo.get_descripcion_display() if obj.grupo else "-"
    get_grupo_display.short_description = "Grupo"

    def get_subgrupo_display(self, obj):
        return obj.subgrupo.get_descripcion_display() if obj.subgrupo else "-"
    get_subgrupo_display.short_description = "Subgrupo"

    def get_clasificacion_display(self, obj):
        return obj.clasificacion.get_descripcion_display() if obj.clasificacion else "-"
    get_clasificacion_display.short_description = "Clasificación"


    actions = ['crear_lote_predeterminado']

    def crear_lote_predeterminado(self, request, queryset):
        """Action para crear un lote predeterminado para productos seleccionados"""
        from datetime import date, timedelta
        
        for producto in queryset:
            # Verificar si ya tiene lotes
            if not producto.lotes.exists():
                lote = ProductoLote.objects.create(
                    producto=producto,
                    lote=f"LOTE-{producto.codigo}-001",
                    fecha_elaboracion=date.today(),
                    vigencia_lote=date.today() + timedelta(days=365),
                    cantidad=100
                )
                self.message_user(
                    request, 
                    f"✅ Lote creado para {producto.nombre}: {lote.lote}", 
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request, 
                    f"ℹ️ {producto.nombre} ya tiene lotes", 
                    level=messages.INFO
                )
    
    crear_lote_predeterminado.short_description = "📦 Crear lote predeterminado"




@admin.register(ProductoLote)
class ProductoLoteAdmin(admin.ModelAdmin):
    list_display = (
        "producto",
        "lote",
        "fecha_elaboracion",
        "vigencia_lote",
        "cantidad_display",  
        "dias_para_vencer",  
        "activo_producto",   
    )
    search_fields = ("producto__codigo", "producto__nombre", "lote")
    list_filter = (
        "producto__grupo__descripcion",
        "producto__subgrupo__descripcion",
        "producto__clasificacion__descripcion",
        "vigencia_lote",
        "producto__activo",  
    )
    ordering = ("producto__nombre", "lote")
    list_per_page = 30
    autocomplete_fields = ['producto']  
    list_select_related = ('producto',)  

    
    readonly_fields = ('dias_para_vencer', 'activo_producto')

    
    fieldsets = (
        ("Información del Lote", {
            "fields": ("producto", "lote", "cantidad")
        }),
        ("Fechas", {
            "fields": ("fecha_elaboracion", "vigencia_lote", "dias_para_vencer")
        }),
        ("Información del Producto", {
            "fields": ("activo_producto",)
        }),
    )

    # ====================== Métodos personalizados MEJORADOS ======================

    @admin.display(description="Cantidad")
    def cantidad_display(self, obj):
        """Muestra la cantidad con colores según el stock"""
        if obj.cantidad > 100:
            return format_html('<span style="color: green; font-weight: bold;">✅ {}</span>', obj.cantidad)
        elif obj.cantidad > 10:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ {}</span>', obj.cantidad)
        elif obj.cantidad > 0:
            return format_html('<span style="color: red; font-weight: bold;">🔴 {}</span>', obj.cantidad)
        else:
            return format_html('<span style="color: gray; font-weight: bold;">❌ {}</span>', obj.cantidad)
    cantidad_display.admin_order_field = "cantidad"

    @admin.display(description="Días para Vencer")
    def dias_para_vencer(self, obj):
        """Calcula días restantes para vencimiento"""
        from datetime import date
        if obj.vigencia_lote:
            dias = (obj.vigencia_lote - date.today()).days
            if dias > 90:
                return format_html('<span style="color: green;">✅ {} días</span>', dias)
            elif dias > 30:
                return format_html('<span style="color: orange;">⚠️ {} días</span>', dias)
            elif dias > 0:
                return format_html('<span style="color: red;">🔴 {} días</span>', dias)
            else:
                return format_html('<span style="color: darkred;">❌ Vencido</span>')
        return "-"

    @admin.display(description="Producto Activo")
    def activo_producto(self, obj):
        return "✅ Sí" if obj.producto.activo else "❌ No"

    
    actions = ['duplicar_lotes', 'ajustar_stock']

    def duplicar_lotes(self, request, queryset):
        """Duplica los lotes seleccionados"""
        for lote in queryset:
            nuevo_lote = ProductoLote.objects.create(
                producto=lote.producto,
                lote=f"{lote.lote}-COPY",
                fecha_elaboracion=lote.fecha_elaboracion,
                vigencia_lote=lote.vigencia_lote,
                cantidad=lote.cantidad
            )
        self.message_user(
            request, 
            f"✅ {queryset.count()} lotes duplicados", 
            level=messages.SUCCESS
        )
    
    duplicar_lotes.short_description = "📋 Duplicar lotes seleccionados"

    def ajustar_stock(self, request, queryset):
        """Ajusta el stock de lotes seleccionados a un valor específico"""
        
        self.message_user(
            request, 
            "ℹ️ Función de ajuste de stock - implementar con formulario personalizado", 
            level=messages.INFO
        )
    
    ajustar_stock.short_description = "📊 Ajustar stock de lotes"