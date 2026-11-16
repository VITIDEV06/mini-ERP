from django.core.validators import RegexValidator
from django.db import models

validar_identificacion = RegexValidator(
    r'^[A-Za-z0-9-]{5,20}$',
    'La identificación debe tener entre 5 y 20 caracteres (letras, números o guion).',
)
validar_telefono = RegexValidator(
    r'^\+?[0-9 ()-]{7,20}$',
    'Teléfono no válido. Use entre 7 y 20 dígitos; se permiten +, espacios, guiones y paréntesis.',
)


class ClienteQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)


class Cliente(models.Model):
    identificacion = models.CharField(
        'cédula / identificación', max_length=20, unique=True, validators=[validar_identificacion],
    )
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    telefono = models.CharField('teléfono', max_length=20, blank=True, validators=[validar_telefono])
    email = models.EmailField('correo electrónico', blank=True)
    direccion = models.CharField('dirección', max_length=255, blank=True)
    fecha_registro = models.DateTimeField('fecha de registro', auto_now_add=True)
    activo = models.BooleanField(default=True)

    objects = ClienteQuerySet.as_manager()

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['apellido', 'nombre']
        indexes = [models.Index(fields=['apellido', 'nombre']), models.Index(fields=['telefono'])]

    def save(self, *args, **kwargs):
        self.identificacion = (self.identificacion or '').strip().upper()
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'

    def __str__(self):
        return f'{self.nombre_completo} ({self.identificacion})'
