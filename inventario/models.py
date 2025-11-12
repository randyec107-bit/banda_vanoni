from django.db import models
from productos.models import Producto



class InventarioProducto(Producto):
    """
    Proxy para representar el inventario de productos,
    diferenciando por lote, fecha de caducidad y ubicación.
    Hereda todos los campos y relaciones de Producto.
    """
    class Meta:
        proxy = True
        verbose_name = "Inventario Producto"
        verbose_name_plural = "Inventario Productos"
        ordering = ['nombre']

    @property
    def cantidad_total(self):
        """Suma todas las cantidades de los lotes asociados al producto."""
        return sum(lote.cantidad for lote in self.lotes.all())

    @property
    def fecha_elaboracion(self):
        """Devuelve la fecha de elaboración más reciente del producto según sus lotes."""
        ultimo_lote = self.lotes.order_by('-fecha_elaboracion').first()
        return ultimo_lote.fecha_elaboracion if ultimo_lote else None

    @property
    def vigencia_lote(self):
        """Devuelve la fecha de vigencia más próxima del producto según sus lotes."""
        ultimo_lote = self.lotes.order_by('vigencia_lote').first()
        return ultimo_lote.vigencia_lote if ultimo_lote else None



class AlmacenProducto(models.Model):
    """
    Gestiona la ubicación física de los productos en almacén.
    Relacionado con Producto mediante OneToOneField.
    Si no se define la bodega, se usa la ubicación del producto.
    """
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name="almacen",
        verbose_name="Producto"
    )
    bodega = models.CharField(max_length=100, verbose_name="Bodega", blank=True, null=True)
    seccion = models.CharField(max_length=50, verbose_name="Sección", blank=True, null=True)
    estante = models.CharField(max_length=50, verbose_name="Estante", blank=True, null=True)

    class Meta:
        verbose_name = "Almacen Producto"
        verbose_name_plural = "Almacenes de Productos"
        ordering = ['producto__nombre']

    def __str__(self):
        return f"{self.producto.nombre} - {self.get_bodega_display()}"

    def get_bodega_display(self):
        """Devuelve la bodega definida o la ubicación del producto si está vacía."""
        return self.bodega or self.producto.ubicacion or "Sin ubicación"

    @property
    def nombre(self):
        """Acceso rápido al nombre del producto."""
        return self.producto.nombre

    @property
    def codigo(self):
        """Acceso rápido al código del producto."""
        return self.producto.codigo

    @property
    def activo(self):
        """Acceso rápido al estado activo del producto."""
        return self.producto.activo
