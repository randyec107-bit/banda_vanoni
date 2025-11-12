# adquisiciones/signals.py
import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Adquisicion

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Adquisicion)
def procesar_adquisicion_confirmada(sender, instance, created, **kwargs):
    """
    Gestiona el inventario según el estado de la adquisición.
    - CONFIRMADO → crea/actualiza lotes en ProductoLote (si no ha sido procesado antes)
    - CANCELADO → revierte lotes en ProductoLote (si estaba procesado)
    
    IMPORTANTE: Usa 'inventario_procesado' 
    """

    # -------- CONFIRMADO → CREAR/ACTUALIZAR LOTES EN ProductoLote --------
    if instance.estado == "CONFIRMADO" and not instance.inventario_procesado:
        try:
            with transaction.atomic():
                for detalle in instance.detalles.all():
                    if not detalle.lote or not detalle.vigencia_lote:
                        logger.warning(
                            f"Detalle omitido en {instance.numero_orden}: "
                            f"Producto {detalle.producto} sin lote o vigencia."
                        )
                        continue

                    
                    lote_obj, created_lote = ProductoLote.objects.get_or_create(
                        producto=detalle.producto,
                        lote=detalle.lote,
                        defaults={
                            "vigencia_lote": detalle.vigencia_lote,
                            "fecha_elaboracion": instance.fecha_arribo,
                            "cantidad": detalle.cantidad
                        }
                    )
                    
                    if not created_lote:
                        # Si el lote ya existe, sumar la cantidad
                        lote_obj.cantidad += detalle.cantidad
                        lote_obj.vigencia_lote = detalle.vigencia_lote
                        lote_obj.save()
                        logger.info(f"Lote existente actualizado: {lote_obj}")
                    else:
                        logger.info(f"Nuevo lote creado: {lote_obj}")

                
                instance.inventario_procesado = True
                
                Adquisicion.objects.filter(pk=instance.pk).update(inventario_procesado=True)
                
                logger.info(f"✅ Lotes creados/actualizados para {instance.numero_orden}. "
                           f"Inventario se sincronizará automáticamente.")
                           
        except Exception as e:
            logger.error(f"❌ Error al procesar adquisición confirmada {instance.numero_orden}: {str(e)}")
            

    # -------- CANCELADO → REVERTIR LOTES EN ProductoLote --------
    elif instance.estado == "CANCELADO" and instance.inventario_procesado:
        try:
            with transaction.atomic():
                for detalle in instance.detalles.all():
                    if not detalle.lote or not detalle.vigencia_lote:
                        logger.warning(
                            f"Detalle omitido al cancelar {instance.numero_orden}: "
                            f"Producto {detalle.producto} sin lote o vigencia."
                        )
                        continue

                    try:
                        
                        lote_obj = ProductoLote.objects.get(
                            producto=detalle.producto,
                            lote=detalle.lote,
                            vigencia_lote=detalle.vigencia_lote,
                        )
                        
                        # Restar la cantidad y eliminar si queda en cero o menos
                        lote_obj.cantidad = max(0, lote_obj.cantidad - detalle.cantidad)
                        if lote_obj.cantidad > 0:
                            lote_obj.save()
                            logger.info(f"Lote actualizado al cancelar: {lote_obj}")
                        else:
                            lote_obj.delete()
                            logger.info(f"Lote eliminado por stock cero: {detalle.producto} - {detalle.lote}")
                            
                    except ProductoLote.DoesNotExist:
                        logger.warning(
                            f"No existe lote para restar en {instance.numero_orden} "
                            f"(Producto {detalle.producto}, Lote {detalle.lote})"
                        )

                
                instance.inventario_procesado = False
                Adquisicion.objects.filter(pk=instance.pk).update(inventario_procesado=False)
                
                logger.info(f"⚠️ Lotes revertidos para {instance.numero_orden}.")
                
        except Exception as e:
            logger.error(f"❌ Error al revertir adquisición cancelada {instance.numero_orden}: {str(e)}")