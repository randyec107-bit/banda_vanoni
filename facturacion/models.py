# facturacion/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Factura(models.Model):
    pedido = models.OneToOneField('pedidos.Pedido', on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=20, unique=True, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero_factura:
            last = Factura.objects.order_by('id').last()
            sec = 1 if not last else int(last.numero_factura.replace("FACT", "")) + 1
            self.numero_factura = f"FACT{sec:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_factura

# Señal para crear factura automáticamente cuando un pedido se aprueba
@receiver(post_save, sender='pedidos.Pedido')
def crear_factura_automaticamente(sender, instance, created, **kwargs):
    """
    Crea automáticamente una factura cuando un pedido es aprobado
    """
    # Verificar si el pedido está aprobado y no tiene factura
    if instance.aprobado and not hasattr(instance, 'factura'):
        try:
            Factura.objects.create(pedido=instance)
            print(f"✅ Factura creada automáticamente para pedido {instance.numero_pedido}")
        except Exception as e:
            print(f"❌ Error al crear factura automática: {e}")