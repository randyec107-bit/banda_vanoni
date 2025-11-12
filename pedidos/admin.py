# pedidos/admin.py
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa
from .models import Pedido, PedidoDetalle, Tracking
from productos.models import Producto, ProductoLote
from django.utils import timezone  
from django import forms

# ✅ NUEVO: Form personalizado para PedidoDetalle con filtro de lotes
class PedidoDetalleForm(forms.ModelForm):
    class Meta:
        model = PedidoDetalle
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ Hacer el campo producto MÁS GRANDE (mismo tamaño que lote)
        self.fields['producto'].widget.attrs.update({
            'style': 'width: 500px; min-width: 500px;',  # ✅ MÁS ANCHO - MISMO TAMAÑO QUE LOTE
            'data-width': '100%'
        })
        
        # ✅ Filtrar lotes por producto seleccionado
        if 'producto' in self.data:
            try:
                producto_id = int(self.data.get('producto'))
                self.fields['lote'].queryset = ProductoLote.objects.filter(
                    producto_id=producto_id
                ).order_by('vigencia_lote')
            except (ValueError, TypeError):
                pass  # Mantener el queryset por defecto
        elif self.instance.pk and self.instance.producto:
            # Si ya existe una instancia, filtrar por su producto
            self.fields['lote'].queryset = ProductoLote.objects.filter(
                producto=self.instance.producto
            ).order_by('vigencia_lote')
        else:
            # Por defecto, mostrar todos los lotes pero limitados
            self.fields['lote'].queryset = ProductoLote.objects.none()
            
        # ✅ Hacer el campo lote más grande también (MISMO TAMAÑO QUE PRODUCTO)
        self.fields['lote'].widget.attrs.update({
            'style': 'width: 500px; min-width: 500px;',  # ✅ MISMO TAMAÑO QUE PRODUCTO
            'data-width': '100%'
        })

class PedidoDetalleInline(admin.TabularInline):
    model = PedidoDetalle
    form = PedidoDetalleForm  # ✅ NUEVO: Usar el form personalizado
    extra = 1
    fields = (
        'producto', 'lote', 'cantidad', 'stock_disponible', 
        'nombre_producto_auto', 'precio1_auto', 'registro_sanitario_auto',
        'ubicacion_auto', 'fecha_elaboracion_auto', 'vigencia_lote_auto', 
        'subtotal_auto'
    )
    readonly_fields = (
        'stock_disponible', 'nombre_producto_auto', 'precio1_auto', 
        'registro_sanitario_auto', 'ubicacion_auto', 'fecha_elaboracion_auto',
        'vigencia_lote_auto', 'subtotal_auto'
    )
    autocomplete_fields = ['producto']  # ✅ Solo producto necesita autocomplete ahora

    @admin.display(description="Stock Disp.")
    def stock_disponible(self, obj):
        if obj.lote:
            return f"{obj.lote.cantidad} unidades"
        elif obj.producto:
            total = sum(lote.cantidad for lote in obj.producto.lotes.all())
            return f"{total} unidades (total producto)"
        return "0 unidades"

    # ✅ NUEVOS MÉTODOS PARA CAMPOS AUTOMÁTICOS
    @admin.display(description="Nombre Producto")
    def nombre_producto_auto(self, obj):
        if obj.pk:
            return obj.nombre_producto
        return "Seleccione producto"

    @admin.display(description="Precio")
    def precio1_auto(self, obj):
        if obj.pk and obj.precio1:
            return f"${obj.precio1:,.2f}"
        return "$0.00"

    @admin.display(description="Registro Sanitario")
    def registro_sanitario_auto(self, obj):
        if obj.pk:
            return obj.registro_sanitario or "-"
        return "-"

    @admin.display(description="Ubicación")
    def ubicacion_auto(self, obj):
        if obj.pk:
            return obj.ubicacion or "-"
        return "-"

    @admin.display(description="Fecha Elaboración")
    def fecha_elaboracion_auto(self, obj):
        if obj.pk and obj.fecha_elaboracion:
            return obj.fecha_elaboracion.strftime("%Y-%m-%d")
        return "-"

    @admin.display(description="Vigencia Lote")
    def vigencia_lote_auto(self, obj):
        if obj.pk and obj.vigencia_lote:
            return obj.vigencia_lote.strftime("%Y-%m-%d")
        return "-"

    @admin.display(description="Subtotal")
    def subtotal_auto(self, obj):
        if obj.pk:
            return f"${obj.subtotal():,.2f}"
        return "$0.00"

    class Media:
        css = {
            'all': ('admin/css/pedido_custom.css',)  # ✅ CSS para campos más grandes
        }
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/pedido_detalle_autofill.js',
            'admin/js/pedido_lotes_filter.js',  # ✅ NUEVO: JavaScript para filtro dinámico
        )

# ============================================================
# ADMIN DE PEDIDOS - CON CHECKBOXES MEJORADOS Y POSICIÓN
# ============================================================
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_pedido',
        'vendedor_display',
        'nombre_cliente',
        'provincia',
        'requiere_envio_display',
        'total_pedido_display',
        'aprobado_visual',
        'pdf_link'
    )
    search_fields = (
        'numero_pedido',
        'cliente__nombre_completo',
        'cliente__numero_documento',
        'provincia',
    )
    list_filter = ('aprobado', 'vendedor', 'provincia', 'fecha_creacion')
    inlines = [PedidoDetalleInline]

    # ✅ CAMBIO: Checkboxes en la misma línea y más grandes
    fieldsets = (
        ("Datos del Pedido", {
            'fields': (
                'vendedor', 'cliente', 'nombre_cliente', 'telefono',
                'correo', 'provincia', 'direccion', 
                'checkboxes_alineados'  # ✅ NUEVO: Campo personalizado para checkboxes
            )
        }),
    )
    readonly_fields = ('nombre_cliente', 'telefono', 'correo', 'checkboxes_alineados')
    list_per_page = 30
    ordering = ('-fecha_creacion',)

    actions = ['aprobar_pedidos', 'desaprobar_pedidos']

    # ✅ NUEVO: Media class para incluir JavaScript de posición
    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/pedido_save_position.js',  # ✅ NUEVO: Script para mantener posición
            'admin/js/pedido_detalle_autofill.js',
            'admin/js/pedido_lotes_filter.js',
        )
        css = {
            'all': ('admin/css/pedido_custom.css',)
        }

    # ✅ CORREGIDO: Método response_add sin modificar HttpResponseRedirect
    def response_add(self, request, obj, post_url_continue=None):
        """Manejar respuesta después de añadir un nuevo pedido"""
        response = super().response_add(request, obj, post_url_continue)
        
        # Si el usuario hizo clic en "Guardar y continuar editando"
        # El JavaScript se encargará de restaurar la posición automáticamente
        return response

    # ✅ CORREGIDO: Método response_change sin modificar HttpResponseRedirect
    def response_change(self, request, obj):
        """Manejar respuesta después de cambiar un pedido existente"""
        response = super().response_change(request, obj)
        
        # Si el usuario hizo clic en "Guardar y continuar editando"
        # El JavaScript se encargará de restaurar la posición automáticamente
        return response

    # ✅ NUEVO: Campo personalizado para checkboxes alineados y más grandes
    def checkboxes_alineados(self, obj):
        requiere_envio_checked = 'checked' if obj.requiere_envio else ''
        aprobado_checked = 'checked' if obj.aprobado else ''
        
        return format_html(
            '''
            <div style="display: flex; gap: 40px; align-items: center; margin: 15px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" id="requiere_envio_big" name="requiere_envio" {} 
                           style="transform: scale(1.8); margin-right: 10px;"
                           onchange="document.getElementById('id_requiere_envio').checked = this.checked;">
                    <label for="requiere_envio_big" style="font-size: 16px; font-weight: bold;">
                        📦 ¿Requiere envío?
                    </label>
                </div>
                
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" id="aprobado_big" name="aprobado" {} 
                           style="transform: scale(1.8); margin-right: 10px;"
                           onchange="document.getElementById('id_aprobado').checked = this.checked;">
                    <label for="aprobado_big" style="font-size: 16px; font-weight: bold; color: #2E86AB;">
                        ✅ Aprobado
                    </label>
                </div>
            </div>
            <script>
                // Sincronizar checkboxes grandes con los originales
                document.addEventListener('DOMContentLoaded', function() {{
                    document.getElementById('requiere_envio_big').checked = document.getElementById('id_requiere_envio').checked;
                    document.getElementById('aprobado_big').checked = document.getElementById('id_aprobado').checked;
                }});
            </script>
            ''',
            requiere_envio_checked, aprobado_checked
        )
    
    checkboxes_alineados.short_description = "Opciones del Pedido"

    # ================== Métodos de display ==================
    @admin.display(description="Vendedor")
    def vendedor_display(self, obj):
        return obj.get_vendedor_display()
    
    @admin.display(description="Envío")
    def requiere_envio_display(self, obj):
        return "✅ Sí" if obj.requiere_envio else "❌ No"

    @admin.display(description="Total")
    def total_pedido_display(self, obj):
        return f"${obj.total_pedido():,.2f}"

    @admin.display(description="Aprobado")
    def aprobado_visual(self, obj):
        color = "green" if obj.aprobado else "red"
        texto = "✅ Aprobado" if obj.aprobado else "❌ Pendiente"
        url = reverse('admin:pedidos_pedido_toggle_aprobado', args=[obj.pk])
        
        # ✅ MEJORA: Agregar tooltip y estilo más claro
        return format_html(
            '<a href="{}" style="color:{}; font-weight:bold; text-decoration:none; padding:4px 8px; border-radius:4px; background-color:{};" '
            'title="Haz clic para cambiar estado">{} {}</a>',
            url, 
            color,
            '#f0f8ff' if obj.aprobado else '#fff0f0',  # Fondo azul claro para aprobado, rojo claro para pendiente
            "✅" if obj.aprobado else "❌",
            "APROBADO" if obj.aprobado else "PENDIENTE"
        )

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        url = reverse('admin:pedidos_pedido_pdf', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank">📄 PDF</a>',
            url
        )

    # ================== URLs personalizadas ==================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/toggle_aprobado/', 
                 self.admin_site.admin_view(self.toggle_aprobado),
                 name='pedidos_pedido_toggle_aprobado'),
            path('<int:pk>/pdf/', 
                 self.admin_site.admin_view(self.pedido_pdf),
                 name='pedidos_pedido_pdf'),
        ]
        return custom_urls + urls

    # ================== Toggle de aprobación CORREGIDO ==================
    def toggle_aprobado(self, request, pk):
        pedido = self.get_object(request, pk)
        if not pedido:
            self.message_user(request, "Pedido no encontrado.", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:pedidos_pedido_changelist'))

        try:
            # Si vamos a aprobar, verificar stock primero
            if not pedido.aprobado:
                print(f"🔔 [ADMIN] Verificando pedido {pedido.numero_pedido} para aprobación")
                
                # Verificar que todos los detalles tengan lote
                detalles_sin_lote = pedido.detalles.filter(lote__isnull=True)
                if detalles_sin_lote.exists():
                    productos_sin_lote = [detalle.producto.nombre for detalle in detalles_sin_lote]
                    self.message_user(
                        request, 
                        f"❌ No se puede aprobar. Productos sin lote: {', '.join(productos_sin_lote)}", 
                        level=messages.ERROR
                    )
                    return HttpResponseRedirect(reverse('admin:pedidos_pedido_change', args=[pedido.pk]))

                # Verificar stock para cada detalle
                for detalle in pedido.detalles.all():
                    print(f"🔔 [ADMIN] Verificando stock: {detalle.producto.nombre} - Lote: {detalle.lote.lote if detalle.lote else 'N/A'}")
                    if detalle.lote and detalle.lote.cantidad < detalle.cantidad:
                        self.message_user(
                            request, 
                            f"❌ Stock insuficiente para {detalle.producto.nombre}. "
                            f"Disponible: {detalle.lote.cantidad}, Solicitado: {detalle.cantidad}", 
                            level=messages.ERROR
                        )
                        return HttpResponseRedirect(reverse('admin:pedidos_pedido_change', args=[pedido.pk]))

            # ✅ CORRECCIÓN: Cambiar estado ANTES de redireccionar
            nuevo_estado = not pedido.aprobado
            pedido.aprobado = nuevo_estado
            pedido.save()

            # Descontar inventario solo si se está APROBANDO
            if nuevo_estado:  # ✅ Usar nuevo_estado en lugar de pedido.aprobado
                try:
                    print(f"🔔 [ADMIN] Ejecutando descontar_inventario() para {pedido.numero_pedido}")
                    pedido.descontar_inventario()
                    self.message_user(
                        request, 
                        f"✅ Pedido {pedido.numero_pedido} APROBADO. Inventario descontado correctamente.", 
                        level=messages.SUCCESS
                    )
                except Exception as e:
                    # Si hay error al descontar, revertir la aprobación
                    pedido.aprobado = False
                    pedido.save()
                    self.message_user(
                        request, 
                        f"❌ Error al descontar inventario: {str(e)}", 
                        level=messages.ERROR
                    )
            else:
                self.message_user(
                    request, 
                    f"⚠️ Pedido {pedido.numero_pedido} DESAPROBADO.", 
                    level=messages.WARNING
                )

            # ✅ CORRECCIÓN: Forzar recarga completa de la página
            return HttpResponseRedirect(reverse('admin:pedidos_pedido_change', args=[pedido.pk]))

        except Exception as e:
            self.message_user(request, f"❌ Error al cambiar estado: {str(e)}", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:pedidos_pedido_changelist'))

    # ================== PDF del Pedido ==================
    def pedido_pdf(self, request, pk):
        pedido = self.get_object(request, pk)
        if not pedido:
            return HttpResponse("Pedido no encontrado.", status=404)

        html = render_to_string("pedidos/pdf_pedido.html", {"pedido": pedido})
        result = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html.encode("utf-8")), dest=result)
        if pisa_status.err:
            return HttpResponse("Error al generar PDF", status=500)
        result.seek(0)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=Pedido_{pedido.numero_pedido}.pdf'
        return response

    # ================== Actions para aprobación masiva ==================
    def aprobar_pedidos(self, request, queryset):
        """Action para aprobar múltiples pedidos"""
        success_count = 0
        error_count = 0
        
        for pedido in queryset:
            try:
                if pedido.aprobado:
                    self.message_user(
                        request, 
                        f"ℹ️ {pedido.numero_pedido} ya estaba aprobado.", 
                        level=messages.INFO
                    )
                    continue
                
                # Verificar detalles
                detalles_sin_lote = pedido.detalles.filter(lote__isnull=True)
                if detalles_sin_lote.exists():
                    self.message_user(
                        request, 
                        f"❌ {pedido.numero_pedido}: {detalles_sin_lote.count()} productos sin lote.", 
                        level=messages.ERROR
                    )
                    error_count += 1
                    continue
                
                # Verificar stock
                stock_ok = True
                for detalle in pedido.detalles.all():
                    if detalle.lote and detalle.lote.cantidad < detalle.cantidad:
                        self.message_user(
                            request, 
                            f"❌ {pedido.numero_pedido}: Stock insuficiente en {detalle.producto.nombre}", 
                            level=messages.ERROR
                        )
                        stock_ok = False
                        break
                
                if not stock_ok:
                    error_count += 1
                    continue
                
                # Aprobar y descontar inventario
                pedido.aprobado = True
                pedido.save()
                pedido.descontar_inventario()
                
                success_count += 1
                self.message_user(
                    request, 
                    f"✅ {pedido.numero_pedido} aprobado correctamente.", 
                    level=messages.SUCCESS
                )
                
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, 
                    f"❌ Error en {pedido.numero_pedido}: {str(e)}", 
                    level=messages.ERROR
                )
        
        if success_count > 0:
            self.message_user(
                request, 
                f"🎉 {success_count} pedidos aprobados exitosamente.", 
                level=messages.SUCCESS
            )
        if error_count > 0:
            self.message_user(
                request, 
                f"❌ {error_count} pedidos no pudieron ser aprobados.", 
                level=messages.ERROR
            )
    
    aprobar_pedidos.short_description = "✅ Aprobar pedidos seleccionados"

    def desaprobar_pedidos(self, request, queryset):
        """Action para desaprobar múltiples pedidos"""
        processed_count = 0
        for pedido in queryset:
            if pedido.aprobado:
                pedido.aprobado = False
                pedido.save()
                processed_count += 1
        
        if processed_count > 0:
            self.message_user(
                request, 
                f"⚠️ {processed_count} pedidos desaprobados.", 
                level=messages.WARNING
            )
        else:
            self.message_user(
                request, 
                f"ℹ️ No hay pedidos aprobados para desaprobar.", 
                level=messages.INFO
            )
    
    desaprobar_pedidos.short_description = "❌ Desaprobar pedidos seleccionados"

# ============================================================
# ADMIN DE TRACKING - SIN CAMBIOS (SE MANTIENE IGUAL)
# ============================================================
@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    list_display = (
        'pedido_numero',
        'cliente_info',
        'inicio_preparacion_checkbox',
        'fin_preparacion_checkbox',
        'responsable_preparacion',
        'responsable_revision',
        'numero_guia',
        'cantidad_cajas',
        'flete',
        'numero_guia_link',
        'fin_despacho_checkbox',
        'cerrado_checkbox',
        'imprimir_etiqueta',
        'ultima_actualizacion',
    )
    
    list_editable = (
        'responsable_preparacion',
        'responsable_revision',
        'numero_guia',
        'cantidad_cajas',
        'flete',
    )
    
    list_display_links = ('pedido_numero',)
    
    search_fields = ('pedido__numero_pedido', 'numero_guia', 'pedido__cliente__nombre_completo')
    list_filter = (
        'inicio_preparacion', 
        'fin_preparacion', 
        'fin_despacho', 
        'cerrado',
        'responsable_preparacion',
        'responsable_revision',
    )
    list_per_page = 25
    
    change_list_template = 'admin/pedidos/tracking_change_list.html'
    
    save_on_top = True
    
    def save_model(self, request, obj, form, change):
        print(f"🔔 [DEBUG] Guardando Tracking {obj.id}")
        print(f"🔔 [DEBUG] Responsable preparación: {obj.responsable_preparacion}")
        print(f"🔔 [DEBUG] Responsable revisión: {obj.responsable_revision}")
        print(f"🔔 [DEBUG] Número guía: {obj.numero_guia}")
        print(f"🔔 [DEBUG] Cantidad cajas: {obj.cantidad_cajas}")
        print(f"🔔 [DEBUG] Flete: {obj.flete}")
        super().save_model(request, obj, form, change)
        print(f"🔔 [DEBUG] Tracking {obj.id} guardado exitosamente")

    # ================== Métodos visuales ==================
    @admin.display(description="Pedido")
    def pedido_numero(self, obj):
        return format_html(
            '<strong>{}</strong>',
            obj.pedido.numero_pedido
        )

    @admin.display(description="Cliente")
    def cliente_info(self, obj):
        pedido = obj.pedido
        return format_html(
            '{}<br><small>📞{} | 📧{}</small>',
            pedido.nombre_cliente,
            pedido.telefono,
            pedido.correo
        )

    @admin.display(description="Etiqueta")
    def imprimir_etiqueta(self, obj):
        return format_html(
            '<a class="button" href="/pedidos/etiqueta/{}/pdf/" target="_blank">🎫 Imprimir</a>',
            obj.pk
        )

    @admin.display(description="Guía Rastreo")
    def numero_guia_link(self, obj):
        """Muestra el link de rastreo CON COPY AUTOMÁTICO"""
        if obj.numero_guia:
            return format_html(
                '''
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="font-weight: bold; background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{}</span>
                    <a href="https://www.tramaco.com.ec/tracking/{}" target="_blank" 
                       style="font-size:12px; text-decoration: none; background: #2196F3; color: white; padding: 2px 6px; border-radius: 3px;"
                       onclick="navigator.clipboard.writeText('{}').then(() => alert('Número copiado: {}')); return true;">
                       🔍 Rastrear
                    </a>
                    <button type="button" onclick="navigator.clipboard.writeText('{}').then(() => alert('Número copiado: {}'));" 
                            style="font-size:10px; background: #4CAF50; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer;">
                        📋 Copiar
                    </button>
                </div>
                ''',
                obj.numero_guia, obj.numero_guia, obj.numero_guia, obj.numero_guia, obj.numero_guia, obj.numero_guia
            )
        return "-"

    @admin.display(description="Última Actualización")
    def ultima_actualizacion(self, obj):
        # Determinar la última acción realizada
        campos = [
            (obj.cerrado, "Cerrado"),
            (obj.fin_despacho, "Despachado"),
            (obj.fin_preparacion, "Preparación Finalizada"),
            (obj.inicio_preparacion, "Preparación Iniciada")
        ]
        
        for campo, texto in campos:
            if campo:
                return format_html(
                    '<small>{}<br>{}</small>',
                    texto,
                    campo.strftime("%Y-%m-%d %H:%M")
                )
        return "Sin acciones"

    # ================== Checkboxes ==================
    def _render_checkbox(self, obj, field, action_name):
        value = getattr(obj, field)
        url = reverse(f'admin:pedidos_tracking_{action_name}', args=[obj.pk])
        
        if value:
            return format_html(
                '<a href="{}" style="display:block; color:green; font-weight:bold;" title="Haz click para cambiar">'
                '✅ {}</a>',
                url, value.strftime("%m/%d %H:%M")
            )
        return format_html(
            '<a href="{}" style="display:block; color:red; font-weight:bold;" title="Haz click para marcar">'
            '❌ Pendiente</a>',
            url
        )

    @admin.display(description="Inicio Prep.")
    def inicio_preparacion_checkbox(self, obj):
        return self._render_checkbox(obj, "inicio_preparacion", "marcar_inicio")

    @admin.display(description="Fin Prep.")
    def fin_preparacion_checkbox(self, obj):
        return self._render_checkbox(obj, "fin_preparacion", "marcar_fin")

    @admin.display(description="Fin Despacho")
    def fin_despacho_checkbox(self, obj):
        return self._render_checkbox(obj, "fin_despacho", "marcar_despacho")

    @admin.display(description="Cerrado")
    def cerrado_checkbox(self, obj):
        return self._render_checkbox(obj, "cerrado", "marcar_cerrado")

    
    actions = [
        'marcar_inicio_preparacion_action',
        'marcar_fin_preparacion_action', 
        'marcar_fin_despacho_action',
        'marcar_cerrado_action',
        'enviar_actualizacion_email'
    ]

    # ================== URLs personalizadas ==================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/inicio/', self.admin_site.admin_view(self.marcar_inicio_preparacion), name='pedidos_tracking_marcar_inicio'),
            path('<int:pk>/fin/', self.admin_site.admin_view(self.marcar_fin_preparacion), name='pedidos_tracking_marcar_fin'),
            path('<int:pk>/despacho/', self.admin_site.admin_view(self.marcar_fin_despacho), name='pedidos_tracking_marcar_despacho'),
            path('<int:pk>/cerrado/', self.admin_site.admin_view(self.marcar_cerrado), name='pedidos_tracking_marcar_cerrado'),
            path('<int:pk>/actualizar_guia/', self.admin_site.admin_view(self.actualizar_numero_guia), name='pedidos_tracking_actualizar_guia'),
        ]
        return custom_urls + urls

    # ================== Acciones de tracking ==================
    def marcar_inicio_preparacion(self, request, pk):
        obj = self.get_object(request, pk)
        if obj and not obj.inicio_preparacion:
            obj.marcar_inicio_preparacion()
            self._enviar_email_actualizacion(request, obj, "inicio_preparacion")
            self.message_user(request, f"✅ Preparación iniciada para {obj.pedido.numero_pedido}", level=messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def marcar_fin_preparacion(self, request, pk):
        obj = self.get_object(request, pk)
        if obj and not obj.fin_preparacion:
            obj.marcar_fin_preparacion()
            self._enviar_email_actualizacion(request, obj, "fin_preparacion")
            self.message_user(request, f"✅ Preparación finalizada para {obj.pedido.numero_pedido}", level=messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def marcar_fin_despacho(self, request, pk):
        obj = self.get_object(request, pk)
        if obj and not obj.fin_despacho:
            obj.marcar_fin_despacho()
            self._enviar_email_actualizacion(request, obj, "fin_despacho")
            self.message_user(request, f"✅ Pedido despachado {obj.pedido.numero_pedido}", level=messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def marcar_cerrado(self, request, pk):
        obj = self.get_object(request, pk)
        if obj and not obj.cerrado:
            obj.marcar_cerrado()
            self._enviar_email_actualizacion(request, obj, "cerrado")
            self.message_user(request, f"✅ Pedido cerrado {obj.pedido.numero_pedido}", level=messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def actualizar_numero_guia(self, request, pk):
        """Maneja la actualización AJAX del número de guía"""
        obj = self.get_object(request, pk)
        if obj and request.method == 'POST':
            nuevo_numero = request.POST.get('numero_guia', '').strip()
            if nuevo_numero != obj.numero_guia:
                obj.numero_guia = nuevo_numero
                obj.save()
                # 🔑 ENVÍO DE EMAIL si se agregó un número de guía
                if nuevo_numero:
                    self._enviar_email_actualizacion(request, obj, "numero_guia")
                self.message_user(request, f"✅ Número de guía actualizado: {nuevo_numero}", level=messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # ================== SISTEMA DE EMAIL ==================
    def _enviar_email_actualizacion(self, request, tracking, accion):
        """
        Envía email al cliente cuando hay actualizaciones en el tracking
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            from django.conf import settings
            
            pedido = tracking.pedido
            cliente_email = pedido.correo
            
            if not cliente_email:
                print(f"⚠️ No hay email para el cliente {pedido.nombre_cliente}")
                return
            
            # Contexto para el template de email
            contexto = {
                'pedido': pedido,
                'tracking': tracking,
                'accion': accion,
                'fecha_actualizacion': timezone.now(),
                'usuario_admin': request.user.get_full_name() or request.user.username,
                'site_name': getattr(settings, 'SITE_NAME', 'Tu Empresa')
            }
            
            # Determinar asunto según la acción
            asuntos = {
                'inicio_preparacion': f'Tu pedido {pedido.numero_pedido} está en preparación',
                'fin_preparacion': f'Tu pedido {pedido.numero_pedido} ha sido preparado',
                'fin_despacho': f'Tu pedido {pedido.numero_pedido} ha sido despachado',
                'cerrado': f'Tu pedido {pedido.numero_pedido} ha sido completado',
                'numero_guia': f'Número de guía asignado - Pedido {pedido.numero_pedido}',
            }
            
            asunto = asuntos.get(accion, f'Actualización de tu pedido {pedido.numero_pedido}')
            
            # Renderizar contenido HTML y texto plano
            html_content = render_to_string('pedidos/email_actualizacion.html', contexto)
            text_content = strip_tags(html_content)
            
            # Configurar y enviar email
            email = EmailMultiAlternatives(
                subject=asunto,
                body=text_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'notificaciones@tuempresa.com.ec'),
                to=[cliente_email],
                reply_to=[getattr(settings, 'DEFAULT_FROM_EMAIL', 'ventas@tuempresa.com.ec')],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            print(f"✅ Email enviado a {cliente_email} para {pedido.numero_pedido} - Acción: {accion}")
            
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            # No mostrar error al usuario para no interrumpir el flujo

    # ================== ACTIONS PARA LISTA ==================
    @admin.action(description="📧 Enviar actualización por email")
    def enviar_actualizacion_email(self, request, queryset):
        for tracking in queryset:
            self._enviar_email_actualizacion(request, tracking, "actualizacion_general")
        self.message_user(request, f"✅ Emails de actualización enviados para {queryset.count()} pedidos", level=messages.SUCCESS)

    @admin.action(description="⏱️ Marcar inicio preparación")
    def marcar_inicio_preparacion_action(self, request, queryset):
        updated_count = 0
        for tracking in queryset:
            if not tracking.inicio_preparacion:
                tracking.marcar_inicio_preparacion()
                self._enviar_email_actualizacion(request, tracking, "inicio_preparacion")
                updated_count += 1
        self.message_user(request, f"✅ Inicio de preparación marcado para {updated_count} pedidos", level=messages.SUCCESS)

    @admin.action(description="✅ Marcar fin preparación")
    def marcar_fin_preparacion_action(self, request, queryset):
        updated_count = 0
        for tracking in queryset:
            if not tracking.fin_preparacion:
                tracking.marcar_fin_preparacion()
                self._enviar_email_actualizacion(request, tracking, "fin_preparacion")
                updated_count += 1
        self.message_user(request, f"✅ Fin de preparación marcado para {updated_count} pedidos", level=messages.SUCCESS)

    @admin.action(description="🚚 Marcar fin despacho")
    def marcar_fin_despacho_action(self, request, queryset):
        updated_count = 0
        for tracking in queryset:
            if not tracking.fin_despacho:
                tracking.marcar_fin_despacho()
                self._enviar_email_actualizacion(request, tracking, "fin_despacho")
                updated_count += 1
        self.message_user(request, f"✅ Fin de despacho marcado para {updated_count} pedidos", level=messages.SUCCESS)

    @admin.action(description="🔒 Marcar como cerrado")
    def marcar_cerrado_action(self, request, queryset):
        updated_count = 0
        for tracking in queryset:
            if not tracking.cerrado:
                tracking.marcar_cerrado()
                self._enviar_email_actualizacion(request, tracking, "cerrado")
                updated_count += 1
        self.message_user(request, f"✅ Cerrado marcado para {updated_count} pedidos", level=messages.SUCCESS)