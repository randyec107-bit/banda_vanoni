# pedidos/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pedido

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Pedido)
def manejar_aprobacion_pedido(sender, instance, created, **kwargs):
    """
    Señal para manejar el descuento de inventario cuando se aprueba un pedido
    """
    if not created and instance.aprobado:
        try:
            
            if instance.detalles.filter(lote__isnull=True).exists():
                logger.warning(f"Pedido {instance.numero_pedido} aprobado pero tiene productos sin lote")
                return
            
            
            instance.descontar_inventario()
            logger.info(f"✅ Inventario descontado para pedido {instance.numero_pedido}")
                
        except Exception as e:
            logger.error(f"❌ Error en señal para pedido {instance.numero_pedido}: {e}")