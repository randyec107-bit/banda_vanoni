from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator, MinValueValidator
from django.core.exceptions import ValidationError

# -----------------------------
# Choices
# -----------------------------
TIPO_PROVEEDOR_CHOICES = [
    ("LOCAL", "Local (Ecuador)"),
    ("EXTERIOR", "Exterior"),
]

TIPO_IDENTIFICACION_CHOICES = [
    ("CEDULA", "Cédula"),
    ("RUC", "RUC"),
    ("PASAPORTE", "Pasaporte"),
    ("ID_TRIBUTARIO", "ID Tributario Extranjero"),
]

TIPO_PRODUCTOS_CHOICES = [
    ("BIENES", "Bienes"),
    ("SERVICIOS", "Servicios"),
    ("AMBOS", "Ambos"),
]

MONEDA_CHOICES = [
    ("USD", "Dólar estadounidense"),
    ("EUR", "Euro"),
    ("OTRA", "Otra"),
]


PAISES_CAPITALES = {
    "Ecuador": "Quito",
    "Colombia": "Bogotá",
    "Perú": "Lima",
    "Chile": "Santiago",
    "Argentina": "Buenos Aires",
    "España": "Madrid",
    "México": "Ciudad de México",
    "Estados Unidos": "Washington D.C.",
    "Alemania": "Berlín",
    "Francia": "París",

}


# -----------------------------
# Validaciones personalizadas
# -----------------------------
def validar_identificacion(value, tipo, tipo_proveedor):
    """Valida la identificación según tipo y proveedor."""
    if tipo_proveedor == "LOCAL":
        if tipo == "CEDULA" and not (value.isdigit() and len(value) == 10):
            raise ValidationError("La Cédula debe tener 10 dígitos.")
        if tipo == "RUC" and not (value.isdigit() and len(value) == 13):
            raise ValidationError("El RUC debe tener 13 dígitos.")
    elif tipo_proveedor == "EXTERIOR":
        if tipo == "PASAPORTE" and not (8 <= len(value) <= 9):
            raise ValidationError("El pasaporte debe tener entre 8 y 9 caracteres.")
        if tipo == "ID_TRIBUTARIO" and len(value) < 5:
            raise ValidationError("El ID Tributario extranjero debe tener al menos 5 caracteres.")


def validar_cuenta_bancaria(value):
    if len(value) < 10:
        raise ValidationError("La cuenta bancaria debe tener al menos 10 dígitos/caracteres.")


# -----------------------------
# Modelo Proveedor
# -----------------------------
class Proveedor(models.Model):
    tipo_proveedor = models.CharField(
        max_length=10,
        choices=TIPO_PROVEEDOR_CHOICES,
        verbose_name="Tipo de Proveedor"
    )
    tipo_identificacion = models.CharField(
        max_length=20,
        choices=TIPO_IDENTIFICACION_CHOICES,
        verbose_name="Tipo de Identificación"
    )
    numero_identificacion = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Identificación"
    )
    razon_social = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        verbose_name="Razón Social / Nombre"
    )

    # Contacto
    email = models.EmailField(
        validators=[EmailValidator()],
        verbose_name="Email"
    )
    telefono = models.IntegerField(
        max_length=10,
        verbose_name="Teléfono"
    )
    direccion = models.CharField(
        max_length=255,
        verbose_name="Dirección"
    )
    pais = models.CharField(
        max_length=100,
        choices=[(p, p) for p in PAISES_CAPITALES.keys()],
        verbose_name="País"
    )
    ciudad = models.CharField(
        max_length=100,
        editable=False,  
        verbose_name="Ciudad (capital)"
    )

    # Datos tributarios y bancarios
    tipo_productos = models.CharField(
        max_length=10,
        choices=TIPO_PRODUCTOS_CHOICES,
        verbose_name="Tipo de Proveedor (Bienes/Servicios/Ambos)"
    )
    moneda_pago = models.CharField(
        max_length=10,
        choices=MONEDA_CHOICES,
        verbose_name="Moneda de Pago"
    )
    cuenta_bancaria = models.CharField(
        max_length=34,
        validators=[validar_cuenta_bancaria],
        verbose_name="Cuenta Bancaria"
    )

    plazo_entrega = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Plazo de Entrega (días hábiles)"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["razon_social"]

    def __str__(self):
        return f"{self.razon_social} ({self.numero_identificacion})"

    def clean(self):
        # Validar identificación
        validar_identificacion(self.numero_identificacion, self.tipo_identificacion, self.tipo_proveedor)

        
        if self.pais in PAISES_CAPITALES:
            self.ciudad = PAISES_CAPITALES[self.pais]
        else:
            self.ciudad = "Capital desconocida"
