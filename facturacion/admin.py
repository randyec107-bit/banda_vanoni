# facturacion/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from .models import Factura

def generar_pdf_factura(factura):
    """
    Genera el PDF de la factura usando la función existente
    """
    try:
        # Simulamos una request para usar tu función existente
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/factura/{factura.id}/pdf/')
        
        # Llamamos a tu función factura_pdf
        pedido = factura.pedido
        html_string = render_to_string("pedidos/pdf_pedido.html", {"pedido": pedido, "factura": factura})
        result = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html_string.encode("UTF-8")), dest=result)
        
        if pisa_status.err:
            raise Exception("Error al generar PDF")
            
        return result.getvalue()
        
    except Exception as e:
        # Fallback: generar un PDF simple en caso de error
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, f"Factura: {factura.numero_factura}")
        p.drawString(100, 730, f"Cliente: {factura.pedido.nombre_cliente}")
        p.drawString(100, 710, f"Pedido: {factura.pedido.numero_pedido}")
        p.drawString(100, 690, f"Fecha: {factura.fecha_creacion.strftime('%d/%m/%Y')}")
        p.drawString(100, 670, "Este es un PDF temporal - Error en generación completa")
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'cliente_nombre', 'cliente_email', 'imprimir_pdf', 'notificar_cliente')
    search_fields = ('numero_factura', 'pedido__nombre_cliente', 'pedido__correo')  
    actions = ['enviar_notificaciones']

    def cliente_nombre(self, obj):
        return obj.pedido.nombre_cliente
    cliente_nombre.short_description = "Cliente"

    def cliente_email(self, obj):
        return obj.pedido.correo or "No tiene email"
    cliente_email.short_description = "Email Cliente"

    def imprimir_pdf(self, obj):
        return format_html(
            '<a class="button" href="/pedidos/factura/{}/pdf/" target="_blank">📄 Imprimir PDF</a>',
            obj.pk
        )
    imprimir_pdf.short_description = "Factura PDF"

    def notificar_cliente(self, obj):
        # Verificar si el cliente tiene email
        if not obj.pedido.correo:
            return format_html(
                '<span style="color: #999; cursor: not-allowed;">📧 Sin email</span>'
            )
        
        return format_html(
            '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 12px;">📧 Notificar</a>',
            f'/admin/facturacion/factura/{obj.id}/notificar/'
        )
    notificar_cliente.short_description = "Notificar"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/notificar/',
                 self.admin_site.admin_view(self.notificar_cliente_view),
                 name='factura_notificar_cliente'),
        ]
        return custom_urls + urls

    def notificar_cliente_view(self, request, object_id):
        """
        Vista para enviar notificación por correo al cliente CON PDF ADJUNTO
        """
        try:
            factura = Factura.objects.get(id=object_id)
            pedido = factura.pedido
            
            # Verificar que el cliente tenga email
            if not pedido.correo:
                messages.error(request, f'El cliente {pedido.nombre_cliente} no tiene email registrado.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/facturacion/factura/'))

            try:
                # Generar el PDF usando tu función existente
                pdf_content = generar_pdf_factura(factura)
                
                # Crear el email con adjunto
                asunto = f'Factura {factura.numero_factura} - Su pedido está listo'
                
                mensaje_html = f"""
                <html>
                <body>
                    <p>Estimado/a <strong>{pedido.nombre_cliente}</strong>,</p>
                    
                    <p>Le informamos que su factura <strong>{factura.numero_factura}</strong> ha sido generada exitosamente.</p>
                    
                    <h3>Detalles del pedido:</h3>
                    <ul>
                        <li><strong>Número de pedido:</strong> {pedido.numero_pedido}</li>
                        <li><strong>Número de factura:</strong> {factura.numero_factura}</li>
                        <li><strong>Fecha:</strong> {factura.fecha_creacion.strftime('%d/%m/%Y')}</li>
                    </ul>
                    
                    <p>Encontrará la factura en PDF adjunta a este correo.</p>
                    
                    <p>Gracias por su preferencia.</p>
                    
                    <p>Atentamente,<br>
                    <strong>El equipo de ventas</strong></p>
                </body>
                </html>
                """
                
                mensaje_texto = f"""
                Estimado/a {pedido.nombre_cliente},

                Le informamos que su factura {factura.numero_factura} ha sido generada exitosamente.

                Detalles del pedido:
                - Número de pedido: {pedido.numero_pedido}
                - Número de factura: {factura.numero_factura}
                - Fecha: {factura.fecha_creacion.strftime('%d/%m/%Y')}

                Encontrará la factura en PDF adjunta a este correo.

                Gracias por su preferencia.

                Atentamente,
                El equipo de ventas
                """

                email = EmailMessage(
                    asunto,
                    mensaje_texto,
                    settings.DEFAULT_FROM_EMAIL,
                    [pedido.correo],
                )
                
                # Opcional: agregar versión HTML
                email.content_subtype = "plain"  # o "html" si quieres usar HTML
                
                # Adjuntar el PDF
                email.attach(
                    f'factura_{factura.numero_factura}.pdf',
                    pdf_content,
                    'application/pdf'
                )
                
                # Enviar el correo
                email.send()
                
                messages.success(request, f'✅ Factura PDF enviada por correo a {pedido.correo}')
                
            except Exception as e:
                messages.error(request, f'❌ Error al generar o enviar el PDF: {str(e)}')
                print(f"Error detallado: {e}")  # Para debugging
                
        except Factura.DoesNotExist:
            messages.error(request, 'Factura no encontrada.')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/facturacion/factura/'))

    # Acción masiva para enviar notificaciones CON PDF
    def enviar_notificaciones(self, request, queryset):
        """
        Acción para enviar notificaciones a múltiples clientes CON PDF ADJUNTO
        """
        exitosos = 0
        errores = 0
        
        for factura in queryset:
            pedido = factura.pedido
            
            if not pedido.correo:
                self.message_user(request, f'❌ {factura.numero_factura}: Cliente sin email', messages.WARNING)
                errores += 1
                continue
            
            try:
                # Generar el PDF usando tu función existente
                pdf_content = generar_pdf_factura(factura)
                
                # Crear el email
                asunto = f'Factura {factura.numero_factura} - Su pedido está listo'
                
                mensaje_texto = f"""
                Estimado/a {pedido.nombre_cliente},

                Le informamos que su factura {factura.numero_factura} ha sido generada exitosamente.

                Detalles del pedido:
                - Número de pedido: {pedido.numero_pedido}
                - Número de factura: {factura.numero_factura}
                - Fecha: {factura.fecha_creacion.strftime('%d/%m/%Y')}

                Encontrará la factura en PDF adjunta a este correo.

                Gracias por su preferencia.

                Atentamente,
                El equipo de ventas
                """

                email = EmailMessage(
                    asunto,
                    mensaje_texto,
                    settings.DEFAULT_FROM_EMAIL,
                    [pedido.correo],
                )
                
                # Adjuntar el PDF
                email.attach(
                    f'factura_{factura.numero_factura}.pdf',
                    pdf_content,
                    'application/pdf'
                )
                
                # Enviar el correo
                email.send()
                exitosos += 1
                self.message_user(request, f'✅ {factura.numero_factura}: Factura enviada a {pedido.correo}', messages.SUCCESS)
                
            except Exception as e:
                self.message_user(request, f'❌ {factura.numero_factura}: Error - {str(e)}', messages.ERROR)
                errores += 1
                print(f"Error detallado en {factura.numero_factura}: {e}")  # Para debugging
        
        if exitosos > 0:
            self.message_user(request, f'✅ {exitosos} facturas enviadas exitosamente', messages.SUCCESS)
        if errores > 0:
            self.message_user(request, f'⚠️ {errores} facturas no pudieron ser enviadas', messages.WARNING)
    
    enviar_notificaciones.short_description = "📧 Enviar facturas PDF por correo a los clientes seleccionados"