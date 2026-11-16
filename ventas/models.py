from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from clientes.models import Cliente
from productos.models import Producto


class Venta(models.Model):
    """
    Cabecera de venta. Una venta confirmada no se edita: solo puede anularse
    mediante ventas.services.anular_venta, que restaura el inventario.
    """

    class Estado(models.TextChoices):
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        ANULADA = 'ANULADA', 'Anulada'

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas')
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ventas')
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    impuesto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.CONFIRMADA, db_index=True)
    observaciones = models.CharField(max_length=255, blank=True)

    # Auditoría de anulación
    anulada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='ventas_anuladas',
    )
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.CharField('motivo de anulación', max_length=255, blank=True)

    class Meta:
        verbose_name = 'venta'
        verbose_name_plural = 'ventas'
        ordering = ['-fecha', '-pk']
        # add/view vienen por defecto; change/delete existen pero no se asignan a ningún rol.
        permissions = [
            ('anular_venta', 'Puede anular ventas confirmadas'),
            ('ver_todas_ventas', 'Puede consultar las ventas de todos los vendedores'),
            ('ver_estadisticas_generales', 'Puede consultar las estadísticas generales'),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(subtotal__gte=0), name='venta_subtotal_no_negativo'),
            models.CheckConstraint(condition=Q(impuesto__gte=0), name='venta_impuesto_no_negativo'),
            models.CheckConstraint(condition=Q(total__gte=0), name='venta_total_no_negativo'),
        ]

    @property
    def numero(self):
        return f'V-{self.pk:06d}' if self.pk else 'V-nueva'

    @property
    def esta_anulada(self):
        return self.estado == self.Estado.ANULADA

    def __str__(self):
        return f'{self.numero} · {self.cliente.nombre_completo}'


class DetalleVenta(models.Model):
    """Línea de venta. Guarda el precio unitario vigente al momento de vender (precio histórico)."""

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_venta')
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'detalle de venta'
        verbose_name_plural = 'detalles de venta'
        constraints = [
            models.UniqueConstraint(fields=['venta', 'producto'], name='detalle_producto_unico_por_venta'),
            models.CheckConstraint(condition=Q(cantidad__gte=1), name='detalle_cantidad_positiva'),
            models.CheckConstraint(condition=Q(precio_unitario__gte=0), name='detalle_precio_no_negativo'),
            models.CheckConstraint(condition=Q(subtotal__gte=0), name='detalle_subtotal_no_negativo'),
        ]

    def __str__(self):
        return f'{self.producto} x {self.cantidad}'
