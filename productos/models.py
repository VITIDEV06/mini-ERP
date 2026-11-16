from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField('descripción', max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ProductoQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)

    def stock_bajo(self):
        return self.filter(stock__lte=F('stock_minimo'))


class Producto(models.Model):
    codigo = models.CharField(
        'código', max_length=30, unique=True,
        validators=[RegexValidator(r'^[A-Za-z0-9._-]+$', 'Use solo letras, números, punto, guion o guion bajo.')],
    )
    nombre = models.CharField(max_length=150, db_index=True)
    descripcion = models.TextField('descripción', blank=True)
    categoria = models.ForeignKey(
        Categoria, verbose_name='categoría', on_delete=models.PROTECT,
        null=True, blank=True, related_name='productos',
    )
    precio_venta = models.DecimalField(
        'precio de venta', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))],
    )
    costo = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))],
    )
    stock = models.PositiveIntegerField('stock actual', default=0)
    stock_minimo = models.PositiveIntegerField('stock mínimo', default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField('fecha de creación', auto_now_add=True)
    actualizado = models.DateTimeField('fecha de actualización', auto_now=True)

    objects = ProductoQuerySet.as_manager()

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['nombre']
        permissions = [('ver_costos', 'Puede ver el costo de los productos')]
        constraints = [
            models.CheckConstraint(condition=Q(stock__gte=0), name='producto_stock_no_negativo'),
            models.CheckConstraint(condition=Q(stock_minimo__gte=0), name='producto_stock_minimo_no_negativo'),
            models.CheckConstraint(condition=Q(precio_venta__gte=0), name='producto_precio_no_negativo'),
            models.CheckConstraint(condition=Q(costo__gte=0), name='producto_costo_no_negativo'),
        ]

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or '').strip().upper()
        super().save(*args, **kwargs)

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    def __str__(self):
        return f'{self.codigo} · {self.nombre}'
