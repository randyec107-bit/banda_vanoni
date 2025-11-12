from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Pedido, Tracking
from xhtml2pdf import pisa
from io import BytesIO
from facturacion.models import Factura
from django.utils import timezone

# PDF del pedido completo
def pedido_pdf(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    html_string = render_to_string(
        "pedidos/pdf_pedido.html",
        {
            "pedido": pedido,
            "now": timezone.now(),  # ⬅️ fecha y hora exacta de impresión
        }
    )
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=Pedido_{pedido.numero_pedido}.pdf'
    return response

# PDF etiqueta 10x5cm
def etiqueta_pdf(request, pk):
    tracking = get_object_or_404(Tracking, pk=pk)
    html_string = render_to_string("pedidos/pdf_etiqueta.html", {"tracking": tracking})
    result = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_string.encode("UTF-8")), dest=result)
    if pisa_status.err:
        return HttpResponse("Error al generar PDF", status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename=Etiqueta_{tracking.pedido.numero_pedido}.pdf'
    return response


def factura_pdf(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    pedido = factura.pedido
    html_string = render_to_string("pedidos/pdf_pedido.html", {"pedido": pedido, "factura": factura})
    result = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_string.encode("UTF-8")), dest=result)
    if pisa_status.err:
        return HttpResponse("Error al generar PDF", status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename=Factura_{factura.numero_factura}.pdf'
    return response
