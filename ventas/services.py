"""
Lógica de negocio de ventas.

Todas las operaciones que tocan inventario se ejecutan dentro de
transaction.atomic() y bloquean las filas de producto con SELECT ... FOR UPDATE
(en orden de id para evitar interbloqueos). Así, si dos vendedores intentan
vender a la vez las últimas unidades, el segundo espera a que termine el
primero y vuelve a validar el stock ya actualizado.

Los precios y totales se calculan siempre aquí, con los datos de la base de
datos; nunca se usan importes enviados por el navegador.
"""

from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from clientes.models import Cliente
from productos.models import Producto

from .models import DetalleVenta, Venta

CENTAVOS = Decimal('0.01')


class VentaError(ValidationError):
    """Error de regla de negocio al registrar o anular una venta."""


def _redondear(valor):
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _consolidar_items(items):
    """Agrupa cantidades del mismo producto: [(id, cant), ...] -> {id: cant_total}."""
    agrupados = OrderedDict()
    for producto_id, cantidad in items:
        cantidad = int(cantidad)
        if cantidad < 1:
            raise VentaError('Las cantidades deben ser mayores que cero.')
        agrupados[int(producto_id)] = agrupados.get(int(producto_id), 0) + cantidad
    if not agrupados:
        raise VentaError('La venta debe contener al menos un producto.')
    return agrupados


@transaction.atomic
def registrar_venta(*, vendedor, cliente_id, items, observaciones=''):
    """
    Registra y confirma una venta descontando inventario.

    items: iterable de (producto_id, cantidad).
    Lanza VentaError si alguna regla no se cumple; en ese caso no se guarda nada.
    """
    if not vendedor.has_perm('ventas.add_venta'):
        raise VentaError('No tiene permiso para registrar ventas.')

    try:
        cliente = Cliente.objects.get(pk=cliente_id, activo=True)
    except Cliente.DoesNotExist:
        raise VentaError('El cliente seleccionado no existe o está inactivo.')

    cantidades = _consolidar_items(items)

    # Bloqueo de filas en orden determinista.
    productos = {
        p.pk: p for p in Producto.objects.select_for_update().filter(pk__in=cantidades.keys()).order_by('pk')
    }

    errores = []
    for producto_id, cantidad in cantidades.items():
        producto = productos.get(producto_id)
        if producto is None or not producto.activo:
            errores.append(f'El producto con id {producto_id} no existe o está inactivo.')
        elif cantidad > producto.stock:
            errores.append(
                f'Stock insuficiente para "{producto.nombre}": disponible {producto.stock}, solicitado {cantidad}.'
            )
    if errores:
        raise VentaError(errores)

    venta = Venta.objects.create(
        cliente=cliente, vendedor=vendedor, observaciones=(observaciones or '').strip()[:255],
    )

    subtotal_venta = Decimal('0.00')
    detalles = []
    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        precio = producto.precio_venta  # precio histórico congelado en el detalle
        subtotal = _redondear(precio * cantidad)
        subtotal_venta += subtotal
        detalles.append(DetalleVenta(
            venta=venta, producto=producto, cantidad=cantidad, precio_unitario=precio, subtotal=subtotal,
        ))
        producto.stock -= cantidad
        producto.save(update_fields=['stock', 'actualizado'])

    DetalleVenta.objects.bulk_create(detalles)

    venta.subtotal = _redondear(subtotal_venta)
    venta.impuesto = Decimal('0.00')  # Regla actual: las ventas no llevan impuesto.
    venta.total = venta.subtotal + venta.impuesto
    venta.save(update_fields=['subtotal', 'impuesto', 'total'])
    return venta


@transaction.atomic
def anular_venta(*, venta_id, usuario, motivo):
    """
    Anula una venta confirmada y devuelve al inventario las cantidades vendidas.
    Solo usuarios con el permiso ventas.anular_venta. Una venta anulada no puede anularse otra vez.
    """
    if not usuario.has_perm('ventas.anular_venta'):
        raise VentaError('No tiene permiso para anular ventas.')

    motivo = (motivo or '').strip()
    if len(motivo) < 5:
        raise VentaError('Indique el motivo de la anulación (mínimo 5 caracteres).')

    try:
        venta = Venta.objects.select_for_update().get(pk=venta_id)
    except Venta.DoesNotExist:
        raise VentaError('La venta no existe.')

    if venta.estado != Venta.Estado.CONFIRMADA:
        raise VentaError('Solo se pueden anular ventas confirmadas. Esta venta ya fue anulada.')

    detalles = list(venta.detalles.all())
    productos = {
        p.pk: p for p in Producto.objects.select_for_update()
        .filter(pk__in=[d.producto_id for d in detalles]).order_by('pk')
    }
    for detalle in detalles:
        producto = productos[detalle.producto_id]
        producto.stock += detalle.cantidad
        producto.save(update_fields=['stock', 'actualizado'])

    venta.estado = Venta.Estado.ANULADA
    venta.anulada_por = usuario
    venta.fecha_anulacion = timezone.now()
    venta.motivo_anulacion = motivo[:255]
    venta.save(update_fields=['estado', 'anulada_por', 'fecha_anulacion', 'motivo_anulacion'])
    return venta


def ventas_visibles_para(usuario):
    """QuerySet de ventas que el usuario puede consultar."""
    qs = Venta.objects.select_related('cliente', 'vendedor')
    if usuario.has_perm('ventas.ver_todas_ventas'):
        return qs
    return qs.filter(vendedor=usuario)
