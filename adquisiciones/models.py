from django.db import models
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from proveedores.models import Proveedor
from productos.models import Producto, ProductoLote
from simple_history.models import HistoricalRecords
from django.db.models.signals import post_save
from django.dispatch import receiver


class Adquisicion(models.Model):
    ESTADO_CHOICES = [
        ("BORRADOR", "Borrador"),
        ("EN_PROCESO", "En Proceso"),
        ("CONFIRMADO", "Confirmado"),
        ("CANCELADO", "Cancelado"),
    ]

    TIPO_CARGA_CHOICES = [
        ("SUELTA", "Suelta"),
        ("EMBALADO", "Embalado"),
        ("PALLETS", "Pallets"),
        ("CONTENEDOR", "Contenedor"),
        ("GRANEL", "Granel"),
    ]

    numero_orden = models.CharField(max_length=20, unique=True, editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_arribo = models.DateField()
    tipo_carga = models.CharField(max_length=20, choices=TIPO_CARGA_CHOICES)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="BORRADOR")
    inventario_procesado = models.BooleanField(default=False, verbose_name="Inventario Procesado")

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["proveedor", "fecha_arribo"],
                name="unique_proveedor_fecha"
            )
        ]

    def __str__(self):
        return f"{self.numero_orden} - {self.proveedor.razon_social} ({self.fecha_arribo})"

    def clean(self):
        # ✅ CORRECCIÓN: Verificar que fecha_arribo no sea None antes de comparar
        if self.fecha_arribo and self.fecha_arribo < date.today():
            raise ValidationError({
                'fecha_arribo': 'La fecha de arribo debe ser hoy o una fecha futura.'
            })

        # ✅ CORRECCIÓN: Solo validar detalles si el objeto ya existe (tiene pk)
        if self.estado == "CONFIRMADO":
            if self.pk and not self.detalles.exists():
                raise ValidationError({
                    'estado': 'No se puede confirmar la adquisición sin detalles.'
                })
            
            # ✅ CORRECCIÓN: Solo validar lotes si el objeto existe
            if self.pk:
                for detalle in self.detalles.all():
                    if not detalle.lote or not detalle.vigencia_lote:
                        raise ValidationError({
                            'estado': 'Todos los productos deben tener lote y vigencia antes de confirmar.'
                        })

    def save(self, *args, **kwargs):
        # 🔑 CORRECCIÓN: Obtener el estado anterior ANTES de generar número de orden
        estado_anterior = None
        if self.pk:
            try:
                estado_anterior = Adquisicion.objects.get(pk=self.pk).estado
            except Adquisicion.DoesNotExist:
                pass

        # Generación automática del número de orden solo para nuevos objetos
        if not self.pk and not self.numero_orden:
            year = date.today().year
            last = Adquisicion.objects.filter(
                numero_orden__startswith=f"ADQ{year}"
            ).order_by("numero_orden").last()
            
            if not last:
                self.numero_orden = f"ADQ{year}_0001"
            else:
                try:
                    last_number = int(last.numero_orden.split("_")[1])
                    self.numero_orden = f"ADQ{year}_{last_number+1:04d}"
                except (IndexError, ValueError):
                    self.numero_orden = f"ADQ{year}_0001"

        # Guardar primero el objeto
        super().save(*args, **kwargs)

        # 🔑 CORRECCIÓN MEJORADA: Actualizar inventario después de guardar
        # Solo si cambió de estado a CONFIRMADO y no se ha procesado
        if (estado_anterior != "CONFIRMADO" and 
            self.estado == "CONFIRMADO" and 
            not self.inventario_procesado):
            
            print(f"🔔 [DEBUG] Cambio detectado: {estado_anterior} → {self.estado}")
            self.actualizar_inventario()

    def actualizar_inventario(self):
        """Actualiza el inventario de lotes cuando se confirma la adquisición"""
        try:
            print(f"[Adquisición] Procesando inventario para {self.numero_orden}")
            
            for detalle in self.detalles.all():
                if not detalle.lote or not detalle.vigencia_lote:
                    print(f"[Adquisición] Saltando detalle sin lote/vigencia: {detalle}")
                    continue
                    
                # 🔑 MEJORADO: Manejo más robusto de lotes existentes
                lote_obj, created = ProductoLote.objects.get_or_create(
                    producto=detalle.producto,
                    lote=detalle.lote,
                    defaults={
                        "vigencia_lote": detalle.vigencia_lote,
                        "fecha_elaboracion": self.fecha_arribo,
                        "cantidad": detalle.cantidad
                    }
                )
                
                if not created:
                    # Si el lote ya existe, sumar la cantidad
                    lote_obj.cantidad += detalle.cantidad
                    lote_obj.vigencia_lote = detalle.vigencia_lote
                    lote_obj.save()
                    print(f"[Adquisición] Lote existente actualizado: {lote_obj}")
                else:
                    print(f"[Adquisición] Nuevo lote creado: {lote_obj}")
            
            # 🔑 CORRECCIÓN: Marcar como procesado
            self.inventario_procesado = True
            # Usar update para evitar recursión en save()
            Adquisicion.objects.filter(pk=self.pk).update(inventario_procesado=True)
            
            print(f"[Adquisición] Inventario procesado exitosamente para {self.numero_orden}")
            
        except Exception as e:
            print(f"[Error Adquisición] No se pudo procesar inventario: {e}")
            # No marcar como procesado si hubo error

    # 🔑 CORRECCIÓN: Método para confirmar la adquisición
    def confirmar(self):
        """Método específico para confirmar la adquisición"""
        if self.estado != "CONFIRMADO":
            self.estado = "CONFIRMADO"
            self.save()  # Esto activará la señal y el procesamiento de inventario
            return True
        return False

    # 🔑 NUEVO: Método para forzar la actualización del estado
    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado y asegura que se procesen los cambios"""
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            self.save()
            return True
        return False

    def puede_confirmar(self):
        """Verifica si la adquisición puede ser confirmada"""
        if not self.detalles.exists():
            return False, "No hay detalles en la adquisición"
        
        for detalle in self.detalles.all():
            if not detalle.lote or not detalle.vigencia_lote:
                return False, f"El producto {detalle.producto.nombre} no tiene lote o vigencia"
        
        return True, "Puede ser confirmada"

    # Propiedades de resumen
    @property
    def total_cantidad(self):
        return sum(detalle.cantidad for detalle in self.detalles.all())

    @property
    def total_peso(self):
        return sum(detalle.peso_total for detalle in self.detalles.all())

    @property
    def total_volumen(self):
        return sum(detalle.volumen_total for detalle in self.detalles.all())

    @property
    def productos_unicos(self):
        return self.detalles.values('producto').distinct().count()


class AdquisicionDetalle(models.Model):
    adquisicion = models.ForeignKey(Adquisicion, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    lote = models.CharField(max_length=100, blank=True, null=True)
    vigencia_lote = models.DateField(blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=1)

    # Medidas físicas opcionales
    peso_unitario_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volumen_unitario_m3 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Detalle de Adquisición"
        verbose_name_plural = "Detalles de Adquisiciones"

    def __str__(self):
        return f"{self.producto.codigo} - {self.producto.nombre} ({self.cantidad})"

    def clean(self):
        errors = {}

        # Cantidad obligatoria
        if self.cantidad <= 0:
            errors['cantidad'] = 'La cantidad debe ser mayor a cero.'

        # Validar relación entre lote y vigencia
        if (self.lote and not self.vigencia_lote) or (self.vigencia_lote and not self.lote):
            errors['lote'] = 'Si ingresas lote, también debes ingresar vigencia (y viceversa).'
            errors['vigencia_lote'] = 'Si ingresas vigencia, también debes ingresar lote (y viceversa).'

        # ✅ CORRECCIÓN: Verificar que vigencia_lote no sea None antes de comparar
        if self.vigencia_lote and self.vigencia_lote <= date.today():
            errors['vigencia_lote'] = 'La vigencia del lote debe ser una fecha futura.'

        # 🔑 NUEVO: Validar que el producto esté activo
        if self.producto and not self.producto.activo:
            errors['producto'] = 'No se puede agregar un producto inactivo a la adquisición.'

        if errors:
            raise ValidationError(errors)

    # Propiedades de medidas calculadas
    @property
    def peso_total(self):
        return (self.peso_unitario_kg or 0) * self.cantidad

    @property
    def volumen_total(self):
        return (self.volumen_unitario_m3 or 0) * self.cantidad


    @property
    def producto_info(self):
        return {
            'codigo': self.producto.codigo,
            'nombre': self.producto.nombre,
            'unidad_medida': self.producto.unidad_medida
        }