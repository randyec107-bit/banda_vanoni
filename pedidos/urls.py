from django.urls import path
from . import views
from django.http import JsonResponse
from productos.models import Producto, ProductoLote
from django.views.decorators.http import require_GET

# Vistas API para el llenado automático en el admin
@require_GET
def api_producto_detalle(request, producto_id):
    """API para obtener datos del producto para llenado automático"""
    try:
        producto = Producto.objects.get(id=producto_id)
        data = {
            'nombre': producto.nombre,
            'precio1': str(producto.precio1),
            'registro_sanitario': producto.registro_sanitario or '',
            'ubicacion': producto.ubicacion or '',
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@require_GET
def api_lote_detalle(request, lote_id):
    """API para obtener datos del lote para llenado automático"""
    try:
        lote = ProductoLote.objects.get(id=lote_id)
        data = {
            'fecha_elaboracion': lote.fecha_elaboracion.strftime('%Y-%m-%d') if lote.fecha_elaboracion else '',
            'vigencia_lote': lote.vigencia_lote.strftime('%Y-%m-%d') if lote.vigencia_lote else '',
            'cantidad': lote.cantidad,
        }
        return JsonResponse(data)
    except ProductoLote.DoesNotExist:
        return JsonResponse({'error': 'Lote no encontrado'}, status=404)

@require_GET
def api_lotes_por_producto(request, producto_id):
    """API para obtener lotes filtrados por producto"""
    try:
        producto = Producto.objects.get(id=producto_id)
        lotes = ProductoLote.objects.filter(producto=producto).order_by('vigencia_lote')
        
        lotes_data = []
        for lote in lotes:
            lotes_data.append({
                'id': lote.id,
                'lote': lote.lote,
                'vigencia_lote': lote.vigencia_lote.strftime('%Y-%m-%d') if lote.vigencia_lote else '',
                'cantidad': lote.cantidad,
                'fecha_elaboracion': lote.fecha_elaboracion.strftime('%Y-%m-%d') if lote.fecha_elaboracion else '',
            })
        
        return JsonResponse({'lotes': lotes_data})
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

urlpatterns = [
    # URLs existentes
    path('pedido/<int:pk>/pdf/', views.pedido_pdf, name='pedido_pdf'),
    path('etiqueta/<int:pk>/pdf/', views.etiqueta_pdf, name='etiqueta_pdf'),
    path('factura/<int:pk>/pdf/', views.factura_pdf, name='factura_pdf'),
    
    # ✅ URLs para el llenado automático en admin
    path('admin/api/producto/<int:producto_id>/', api_producto_detalle, name='api_producto_detalle'),
    path('admin/api/lote/<int:lote_id>/', api_lote_detalle, name='api_lote_detalle'),
    path('admin/api/lotes_por_producto/<int:producto_id>/', api_lotes_por_producto, name='api_lotes_por_producto'),
]