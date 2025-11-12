from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone  # 🔑 Import necesario para default=timezone.now

# ============================================================
# ========== CHOICES: GRUPOS, SUBGRUPOS, CLASIFICACIONES
# ============================================================

GRUPO_CHOICES = [
    ('MATERIAL_QUIRURGICO', 'Material Quirúrgico y Hospitalario'),
    ('MEDICAMENTOS', 'Medicamentos y Farmacéuticos'),
    ('EQUIPO_MEDICO', 'Equipo Médico y Diagnóstico'),
    ('MATERIAL_CURACION', 'Material de Curación y Desechables'),
    ('PRODUCTOS_HIGIENE', 'Productos de Higiene y Asepsia'),
]

SUBGRUPO_CHOICES = [
    ('GUANTES', 'Guantes de Examen y Quirúrgicos'),
    ('JERINGAS', 'Jeringas y Agujas Estériles'),
    ('GASAS', 'Gasas y Apósitos'),
    ('SONDAS', 'Sondas y Catéteres'),
    ('SUTURAS', 'Suturas y Material de Sutura'),
    ('SOLUCIONES_IV', 'Soluciones Intravenosas'),
    ('ANTISEPTICOS', 'Antisépticos y Desinfectantes'),
    ('VENDAJES', 'Vendajes e Inmovilizadores'),
]

CLASIFICACION_CHOICES = [
    ('GUANTES_LATEX_ESTERILES', 'Guantes de Látex Estériles'),
    ('GUANTES_NITRILO_NO_ESTERILES', 'Guantes de Nitrilo No Estériles'),
    ('JERINGAS_3ML', 'Jeringas Desechables 3ml'),
    ('JERINGAS_5ML', 'Jeringas Desechables 5ml'),
    ('JERINGAS_10ML', 'Jeringas Desechables 10ml'),
    ('AGUJAS_21G', 'Agujas Hipodérmicas 21G'),
    ('AGUJAS_23G', 'Agujas Hipodérmicas 23G'),
    ('AGUJAS_25G', 'Agujas Hipodérmicas 25G'),
    ('GASAS_10x10', 'Gasas Estériles 10x10'),
    ('GASAS_20x20', 'Gasas Estériles 20x20'),
    ('APOSITOS_NO_ADHERENTES', 'Apósitos No Adherentes'),
    ('SONDAS_FOLEY', 'Sondas Foley Pediátricas/Adultas'),
    ('CATETER_IV', 'Catéteres Intravenosos'),
    ('SUTURAS_NYLON', 'Suturas Nylon'),
    ('SUTURAS_SEDA', 'Suturas Seda'),
    ('SUTURAS_POLIESTER', 'Suturas Poliéster'),
    ('SOLUCION_SALINA', 'Solución Salina 0.9%'),
    ('SOLUCION_GLUCO_5', 'Solución Glucosada 5%'),
    ('ALCOHOL_70', 'Alcohol Isopropílico 70%'),
    ('POVIDONA_YODADA', 'Povidona Yodada'),
    ('VENDAJE_ELASTICO', 'Vendajes Elásticos 10cm, 15cm'),
    ('VENDAJE_YESO', 'Vendajes de Yeso 5cm, 10cm'),
]

# ============================================================
# ========== MODELOS JERÁRQUICOS
# ============================================================

class GrupoProducto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de Grupo")
    descripcion = models.CharField(max_length=200, choices=GRUPO_CHOICES, verbose_name="Descripción del Grupo")
    proveedor = models.CharField(max_length=200, verbose_name="Proveedor Asociado", blank=True, null=True)

    class Meta:
        verbose_name = "Grupo de Producto"
        verbose_name_plural = "Grupos de Productos"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.get_descripcion_display()} ({self.codigo})"


class SubgrupoProducto(models.Model):
    grupo = models.ForeignKey(GrupoProducto, on_delete=models.CASCADE, related_name="subgrupos", verbose_name="Grupo")
    codigo = models.CharField(max_length=50, verbose_name="Código de Subgrupo")
    descripcion = models.CharField(max_length=200, choices=SUBGRUPO_CHOICES, verbose_name="Descripción del Subgrupo")
    proveedor = models.CharField(max_length=200, verbose_name="Proveedor Asociado", blank=True, null=True)

    class Meta:
        unique_together = ("grupo", "codigo")
        verbose_name = "Subgrupo de Producto"
        verbose_name_plural = "Subgrupos de Productos"
        ordering = ['grupo__codigo', 'codigo']

    def __str__(self):
        return f"{self.grupo.get_descripcion_display()} – {self.get_descripcion_display()}"


class ClasificacionProducto(models.Model):
    subgrupo = models.ForeignKey(SubgrupoProducto, on_delete=models.CASCADE, related_name="clasificaciones", verbose_name="Subgrupo")
    codigo = models.CharField(max_length=50, verbose_name="Código de Clasificación")
    descripcion = models.CharField(max_length=200, choices=CLASIFICACION_CHOICES, verbose_name="Descripción de Clasificación")
    proveedor = models.CharField(max_length=200, verbose_name="Proveedor Asociado", blank=True, null=True)

    class Meta:
        unique_together = ("subgrupo", "codigo")
        verbose_name = "Clasificación de Producto"
        verbose_name_plural = "Clasificaciones de Productos"
        ordering = ['subgrupo__grupo__codigo', 'subgrupo__codigo', 'codigo']

    def __str__(self):
        return f"{self.subgrupo.get_descripcion_display()} – {self.get_descripcion_display()}"


# ============================================================
# ========== PRODUCTO PRINCIPAL
# ============================================================

class Producto(models.Model):
    UBICACION_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('OUTLET', 'Outlet'),
        ('CUARENTENA', 'Cuarentena'),
    ]

    # 🔑 Temporalmente permiten NULL para migración sin errores
    grupo = models.ForeignKey(
        GrupoProducto,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Grupo",
        null=True,
        blank=True
    )
    subgrupo = models.ForeignKey(
        SubgrupoProducto,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Subgrupo",
        null=True,
        blank=True
    )
    clasificacion = models.ForeignKey(
        ClasificacionProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
        verbose_name="Clasificación"
    )

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del Producto")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    descripcion = models.TextField(verbose_name="Descripción Detallada", blank=True, null=True)

    registro_sanitario = models.CharField(max_length=100, verbose_name="Registro Sanitario", blank=True, null=True)
    vigencia_registro = models.DateField(verbose_name="Vigencia del Registro Sanitario", blank=True, null=True)
    proveedor_principal = models.CharField(max_length=200, verbose_name="Proveedor Principal", blank=True, null=True)
    
    ubicacion = models.CharField(max_length=20, choices=UBICACION_CHOICES, verbose_name="Ubicación", default='PRINCIPAL')
    presentacion = models.CharField(max_length=200, verbose_name="Presentación", blank=True, null=True)
    unidad_medida = models.CharField(max_length=50, verbose_name="Unidad de Medida", blank=True, null=True)

    ean13 = models.CharField(max_length=13, verbose_name="Código EAN-13", blank=True, null=True)
    ean14 = models.CharField(max_length=14, verbose_name="Código EAN-14", blank=True, null=True)

    precio1 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio 1")
    precio2 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio 2")
    precio3 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio 3")
    precio_especial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Especial", blank=True, null=True)

    stock_minimo = models.PositiveIntegerField(verbose_name="Stock Mínimo", default=0)
    activo = models.BooleanField(default=True, verbose_name="Activo")

    # 🔑 Solo default=timezone.now, sin auto_now_add
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# ============================================================
# ========== LOTES DE PRODUCTOS
# ============================================================

class ProductoLote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="lotes", verbose_name="Producto")
    lote = models.CharField(max_length=50, verbose_name="Número de Lote")
    fecha_elaboracion = models.DateField(verbose_name="Fecha de Elaboración", blank=True, null=True)
    vigencia_lote = models.DateField(verbose_name="Vigencia del Lote", blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=0, verbose_name="Cantidad Disponible")

    class Meta:
        unique_together = ('producto', 'lote', 'vigencia_lote')
        verbose_name = "Lote de Producto"
        verbose_name_plural = "Lotes de Productos"
        ordering = ['vigencia_lote']

    def __str__(self):
        return f"{self.producto.nombre} - Lote {self.lote} ({self.cantidad} unidades)"


# ============================================================
# ========== INVENTARIO AUTOMÁTICO
# ============================================================

@receiver(post_save, sender=ProductoLote)
def sincronizar_inventario(sender, instance, created, **kwargs):
    """
    Sincroniza automáticamente el stock del inventario
    cada vez que se crea o actualiza un lote.
    """
    try:
        from inventario.models import InventarioProducto
        inventario, creado = InventarioProducto.objects.get_or_create(
            producto=instance.producto,
            lote=instance.lote,
            vigencia_lote=instance.vigencia_lote,
            defaults={'cantidad': instance.cantidad}
        )
        if not creado:
            inventario.cantidad = instance.cantidad
            inventario.save(update_fields=['cantidad'])
    except Exception as e:
        print(f"[Error sincronizando inventario] {e}")
