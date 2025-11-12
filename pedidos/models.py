from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from clientes.models import Cliente
from productos.models import Producto, ProductoLote
from inventario.models import InventarioProducto
from django.utils import timezone

# --------------------- CHOICES ---------------------
VENDEDORES_CHOICES = [
    (1, "Angela Davila"),
    (2, "Rocio Leon"),
    (3, "Edwin Davila"),
    (4, "Rafael Clavijo"),
    (5, "Veronica Gomez"),
    (6, "Maria Susana"),
    (7, "Jazzmin Gonzales"),
]

RESPONSABLES_CHOICES = [
    ("Randy", "Randy"),
    ("Esteban", "Esteban"),
    ("Rafael", "Rafael"),
    ("Guillermo", "Guillermo"),
    ("Edwin", "Edwin"),
    ("Orlando", "Orlando"),
]

# Provincias del Ecuador
PROVINCIAS_CHOICES = [
    ("Azuay", "Azuay"),
    ("Bolívar", "Bolívar"),
    ("Cañar", "Cañar"),
    ("Carchi", "Carchi"),
    ("Chimborazo", "Chimborazo"),
    ("Cotopaxi", "Cotopaxi"),
    ("El Oro", "El Oro"),
    ("Esmeraldas", "Esmeraldas"),
    ("Galápagos", "Galápagos"),
    ("Guayas", "Guayas"),
    ("Imbabura", "Imbabura"),
    ("Loja", "Loja"),
    ("Los Ríos", "Los Ríos"),
    ("Manabí", "Manabí"),
    ("Morona Santiago", "Morona Santiago"),
    ("Napo", "Napo"),
    ("Orellana", "Orellana"),
    ("Pastaza", "Pastaza"),
    ("Pichincha", "Pichincha"),
    ("Santa Elena", "Santa Elena"),
    ("Santo Domingo", "Santo Domingo"),
    ("Sucumbíos", "Sucumbíos"),
    ("Tungurahua", "Tungurahua"),
    ("Zamora Chinchipe", "Zamora Chinchipe"),
]

# --------------------- PEDIDO ---------------------
class Pedido(models.Model):
    vendedor = models.IntegerField(choices=VENDEDORES_CHOICES)
    numero_pedido = models.CharField(max_length=20, unique=True, editable=False)

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre_cliente = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    correo = models.EmailField(blank=True)

    provincia = models.CharField(max_length=50, choices=PROVINCIAS_CHOICES, blank=True, null=True)
    direccion = models.TextField(blank=True)
    requiere_envio = models.BooleanField(default=False, verbose_name="¿Requiere envío?")

    aprobado = models.BooleanField(default=False, verbose_name="Aprobado")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Mantiene autollenado de datos del cliente (excepto dirección),
        y genera numeración automática por vendedor.
        """
        if self.cliente:
            self.nombre_cliente = self.cliente.nombre_completo or ""
            self.telefono = self.cliente.telefono_movil or ""
            self.correo = self.cliente.email or ""
            # NOTA: dirección ya se ingresa manualmente

        
        if not self.numero_pedido:
            # Intentar generar un número único
            for attempt in range(10):  # Máximo 10 intentos
                try:
                    # Buscar el último pedido del mismo vendedor
                    last_pedido = Pedido.objects.filter(vendedor=self.vendedor).order_by("-id").first()
                    
                    if last_pedido and last_pedido.numero_pedido:
                        try:
                            # Extraer el número secuencial del último pedido
                            last_number = int(last_pedido.numero_pedido.split("-PED")[-1])
                            new_number = last_number + 1
                        except (ValueError, IndexError):
                            new_number = 1
                    else:
                        new_number = 1
                    
                    # Generar el nuevo número de pedido
                    self.numero_pedido = f"{self.vendedor}-PED{new_number:04d}"
                    
                    
                    if Pedido.objects.filter(numero_pedido=self.numero_pedido).exists():
                        if attempt < 9:  # No es el último intento
                            continue  # Reintentar con nuevo número
                        else:
                            # Último intento: usar timestamp como fallback
                            import time
                            timestamp = int(time.time())
                            self.numero_pedido = f"{self.vendedor}-PED{timestamp}"
                    
                    
                    super().save(*args, **kwargs)
                    
                    
                    Tracking.objects.get_or_create(pedido=self)
                    
                    return  # Salir si se guardó correctamente
                    
                except IntegrityError:
                    # Si hay duplicado, limpiar el número y reintentar
                    if attempt < 9:  
                        self.numero_pedido = None
                        continue
                    else:
                        # Último intento: usar timestamp como fallback
                        import time
                        timestamp = int(time.time())
                        self.numero_pedido = f"{self.vendedor}-PED{timestamp}"
                        super().save(*args, **kwargs)
                        
                        
                        Tracking.objects.get_or_create(pedido=self)
                        return
        else:
            # Si ya tiene número, guardar normalmente
            super().save(*args, **kwargs)

    def total_pedido(self):
        """Calcula el total sumando los subtotales de todos los detalles"""
        try:
            total = sum(detalle.subtotal() for detalle in self.detalles.all())
            return total
        except Exception as e:
            print(f"Error calculando total del pedido: {e}")
            return 0

    def descontar_inventario(self):
        """Descontar del inventario al aprobar el pedido - VERSIÓN CORREGIDA"""
        try:
            print(f"🔔 [PEDIDO] Iniciando descuento de inventario para {self.numero_pedido}")
            print(f"🔔 [PEDIDO] Tiene {self.detalles.count()} detalles")
            
            with transaction.atomic():
                for detalle in self.detalles.all():
                    print(f"🔔 [PEDIDO] Procesando detalle: {detalle.producto.nombre}")
                    
                    if not detalle.lote:
                        print(f"❌ [PEDIDO] ERROR: Detalle sin lote asignado: {detalle.producto.nombre}")
                        raise ValidationError(f"El producto {detalle.producto.nombre} no tiene lote asignado")
                    
                    lote = detalle.lote
                    cantidad_a_descontar = detalle.cantidad
                    
                    print(f"🔔 [PEDIDO] Producto: {lote.producto.nombre}")
                    print(f"🔔 [PEDIDO] Lote: {lote.lote}")
                    print(f"🔔 [PEDIDO] Stock actual: {lote.cantidad}")
                    print(f"🔔 [PEDIDO] Cantidad a descontar: {cantidad_a_descontar}")
                    
                    # Verificar stock disponible
                    if lote.cantidad < cantidad_a_descontar:
                        error_msg = f"Stock insuficiente para {lote.producto.nombre}. Disponible: {lote.cantidad}, Solicitado: {cantidad_a_descontar}"
                        print(f"❌ [PEDIDO] {error_msg}")
                        raise ValidationError(error_msg)
                    
                    
                    lote.cantidad -= cantidad_a_descontar
                    lote.save()
                    
                    print(f"✅ [PEDIDO] Lote actualizado: {lote.lote}")
                    print(f"✅ [PEDIDO] Nuevo stock: {lote.cantidad}")
                
                print(f"🎉 [PEDIDO] Inventario descontado exitosamente para {self.numero_pedido}")
                
        except Exception as e:
            print(f"❌ [PEDIDO] Error al descontar inventario: {e}")
            raise

    def __str__(self):
        return self.numero_pedido

# --------------------- DETALLE PEDIDO ---------------------
class PedidoDetalle(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    lote = models.ForeignKey(ProductoLote, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)

    nombre_producto = models.CharField(max_length=150, blank=True)
    precio1 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    registro_sanitario = models.CharField(max_length=100, blank=True)
    ubicacion = models.CharField(max_length=50, blank=True)
    fecha_elaboracion = models.DateField(blank=True, null=True)
    vigencia_lote = models.DateField(blank=True, null=True)

    def clean(self):
        """Validación para asegurar que hay stock suficiente"""
        if self.pk and self.lote and self.cantidad:
            if self.lote.cantidad < self.cantidad:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {self.lote.cantidad}, "
                    f"Solicitado: {self.cantidad}"
                )

    def save(self, *args, **kwargs):
        if self.producto:
            self.nombre_producto = self.producto.nombre or ""
            self.precio1 = self.producto.precio1 or 0
            self.registro_sanitario = self.producto.registro_sanitario or ""

        if self.lote:
            self.ubicacion = self.lote.producto.ubicacion or ""
            self.fecha_elaboracion = self.lote.fecha_elaboracion
            self.vigencia_lote = self.lote.vigencia_lote

        # Validar antes de guardar
        self.clean()
        
        super().save(*args, **kwargs)

    def subtotal(self):
        return (self.cantidad or 0) * (self.precio1 or 0)

    def __str__(self):
        return f"{self.producto.codigo} - {self.cantidad}"

# --------------------- TRACKING ---------------------
class Tracking(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="tracking")

    inicio_preparacion = models.DateTimeField(blank=True, null=True)
    fin_preparacion = models.DateTimeField(blank=True, null=True)
    responsable_preparacion = models.CharField(max_length=50, choices=RESPONSABLES_CHOICES, blank=True)
    responsable_revision = models.CharField(max_length=50, choices=RESPONSABLES_CHOICES, blank=True)

    numero_guia = models.CharField(max_length=50, blank=True)
    cantidad_cajas = models.PositiveIntegerField(blank=True, null=True)
    flete = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    fin_despacho = models.DateTimeField(blank=True, null=True)
    cerrado = models.DateTimeField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """✅ NUEVO: Guardar automáticamente sin necesidad de crear manualmente"""
        # Si es un nuevo registro, asegurarse de que el pedido existe
        if not self.pk and not self.pedido_id:
            raise ValidationError("El tracking debe estar asociado a un pedido")
        
        super().save(*args, **kwargs)

    def marcar_inicio_preparacion(self):
        if not self.inicio_preparacion:
            self.inicio_preparacion = timezone.now()
            self.save(update_fields=["inicio_preparacion"])

    def marcar_fin_preparacion(self):
        if not self.fin_preparacion:
            self.fin_preparacion = timezone.now()
            self.save(update_fields=["fin_preparacion"])

    def marcar_fin_despacho(self):
        if not self.fin_despacho:
            self.fin_despacho = timezone.now()
            self.save(update_fields=["fin_despacho"])

    def marcar_cerrado(self):
        if not self.cerrado:
            self.cerrado = timezone.now()
            self.save(update_fields=["cerrado"])

            # Crear factura automáticamente si no existe
            try:
                from facturacion.models import Factura
                if not hasattr(self.pedido, "factura"):
                    Factura.objects.create(pedido=self.pedido)
                    print(f"✅ Factura creada automáticamente al cerrar tracking para {self.pedido.numero_pedido}")
            except Exception as e:
                print(f"⚠️ Error al crear factura automática: {e}")

    def __str__(self):
        return f"Tracking de {self.pedido.numero_pedido}"

# --------------------- SEÑAL PARA CREAR FACTURA AUTOMÁTICA ---------------------
@receiver(post_save, sender=Pedido)
def crear_factura_automaticamente(sender, instance, created, **kwargs):
    """
    Crea automáticamente una factura cuando un pedido es aprobado
    """
    # Verificar si el pedido está aprobado y no tiene factura
    if instance.aprobado and not hasattr(instance, 'factura'):
        try:
            from facturacion.models import Factura
            Factura.objects.create(pedido=instance)
            print(f"✅ Factura creada automáticamente para pedido {instance.numero_pedido}")
        except Exception as e:
            print(f"❌ Error al crear factura automática: {e}")