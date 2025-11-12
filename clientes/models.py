# clientes/models.py
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator, EmailValidator
from django.core.exceptions import ValidationError

# Opciones de tipo de documento
TIPO_DOCUMENTO_CHOICES = [
    ("CEDULA", "Cédula"),
    ("PASAPORTE", "Pasaporte"),
    ("RUC", "RUC"),
]

# Provincias de Ecuador
PROVINCIAS_ECUADOR = [
    ("AZUAY", "Azuay"),
    ("BOLIVAR", "Bolívar"),
    ("CAÑAR", "Cañar"),
    ("CARCHI", "Carchi"),
    ("CHIMBORAZO", "Chimborazo"),
    ("COTOPAXI", "Cotopaxi"),
    ("EL_ORO", "El Oro"),
    ("ESMERALDAS", "Esmeraldas"),
    ("GUAYAS", "Guayas"),
    ("IMBABURA", "Imbabura"),
    ("LOJA", "Loja"),
    ("LOS_RIOS", "Los Ríos"),
    ("MANABI", "Manabí"),
    ("MORONA_SANTIAGO", "Morona Santiago"),
    ("NAPO", "Napo"),
    ("PASTAZA", "Pastaza"),
    ("PICHINCHA", "Pichincha"),
    ("TUNGURAHUA", "Tungurahua"),
    ("ZAMORA_CHINCHIPE", "Zamora Chinchipe"),
    ("SUCUMBIOS", "Sucumbíos"),
    ("ORELLANA", "Orellana"),
    ("SANTO_DOMINGO", "Santo Domingo de los Tsáchilas"),
    ("GALAPAGOS", "Galápagos"),
]

# Validadores
solo_letras_validator = RegexValidator(
    regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$',
    message='El campo solo puede contener letras y espacios.'
)

telefono_validator = RegexValidator(
    regex=r'^\+?\d{7,15}$',
    message='Número de teléfono inválido. Puede incluir código de país (+593).'
)


def validar_documento(value, tipo_documento):
    if tipo_documento == "CEDULA" and not (value.isdigit() and len(value) == 10):
        raise ValidationError("Cédula debe tener 10 dígitos numéricos.")
    elif tipo_documento == "RUC" and not (value.isdigit() and len(value) == 13):
        raise ValidationError("RUC debe tener 13 dígitos numéricos.")
    elif tipo_documento == "PASAPORTE" and not (8 <= len(value) <= 9):
        raise ValidationError("Pasaporte debe tener 8 o 9 caracteres alfanuméricos.")


class Cliente(models.Model):
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name="Tipo de Documento"
    )
    numero_documento = models.CharField(
        max_length=13,
        verbose_name="Número de Documento"
    )
    nombre_completo = models.CharField(
        max_length=100,
        validators=[solo_letras_validator, MinLengthValidator(2)],
        verbose_name="Nombre Completo"
    )
    telefono_movil = models.CharField(
        max_length=15,
        validators=[telefono_validator],
        verbose_name="Teléfono Móvil",
        blank=True,
        null=True
    )
    email = models.EmailField(
        blank=True,
        null=True,
        validators=[EmailValidator()],
        verbose_name="Email"
    )
    direccion = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(5)],
        verbose_name="Dirección",
        blank=True,
        null=True
    )
    provincia = models.CharField(
        max_length=50,
        choices=PROVINCIAS_ECUADOR,
        verbose_name="Provincia"
    )

    
    aplica_descuento = models.BooleanField(
        default=False,
        verbose_name="Aplica Descuento"
    )
    requiere_envio = models.BooleanField(
        default=False,
        verbose_name="Requiere Envío"
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre_completo"]
        constraints = [
            models.UniqueConstraint(fields=["tipo_documento", "numero_documento"], name="unique_tipo_numero")
        ]

    def __str__(self):
        return f"{self.nombre_completo} ({self.numero_documento})"

    def clean(self):
        validar_documento(self.numero_documento, self.tipo_documento)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    
    @property
    def nombre_corto(self):
        return self.nombre_completo.split()[0]

    @property
    def numero_documento_formateado(self):
        if self.tipo_documento == "RUC" and len(self.numero_documento) == 13:
            return f"{self.numero_documento[:2]}-{self.numero_documento[2:10]}-{self.numero_documento[10:]}"
        return self.numero_documento
