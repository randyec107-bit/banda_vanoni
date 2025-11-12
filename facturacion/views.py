# views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from .models import Factura

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
