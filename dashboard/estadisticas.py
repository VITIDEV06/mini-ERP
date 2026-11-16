"""
Cálculo de indicadores del dashboard.

La agrupación por día/mes se hace en Python con la zona horaria local en lugar
de usar TruncDate en MySQL: en Windows MySQL suele no tener cargadas las tablas
de zonas horarias y CONVERT_TZ devolvería NULL.
"""

from collections import OrderedDict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from clientes.models import Cliente
from productos.models import Producto
from ventas.models import DetalleVenta, Venta

MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def _ventas_por_dia(qs, dias=30):
    hoy = timezone.localdate()
    inicio = hoy - timedelta(days=dias - 1)
    serie = OrderedDict(((inicio + timedelta(days=i)), Decimal('0')) for i in range(dias))
    desde = timezone.make_aware(datetime.combine(inicio, time.min))
    for fecha, total in qs.filter(fecha__gte=desde).values_list('fecha', 'total'):
        dia = timezone.localtime(fecha).date()
        if dia in serie:
            serie[dia] += total
    return {
        'labels': [d.strftime('%d/%m') for d in serie],
        'valores': [float(v) for v in serie.values()],
    }


def _ventas_por_mes(qs, meses=12):
    hoy = timezone.localdate()
    claves = []
    anio, mes = hoy.year, hoy.month
    for _ in range(meses):
        claves.append((anio, mes))
        mes -= 1
        if mes == 0:
            anio, mes = anio - 1, 12
    claves.reverse()
    serie = OrderedDict((c, Decimal('0')) for c in claves)
    primer = claves[0]
    desde = timezone.make_aware(datetime(primer[0], primer[1], 1))
    for fecha, total in qs.filter(fecha__gte=desde).values_list('fecha', 'total'):
        local = timezone.localtime(fecha)
        clave = (local.year, local.month)
        if clave in serie:
            serie[clave] += total
    return {
        'labels': [f'{MESES[m - 1]} {str(a)[2:]}' for a, m in serie],
        'valores': [float(v) for v in serie.values()],
    }


def _resumen_ventas(qs):
    confirmadas = qs.filter(estado=Venta.Estado.CONFIRMADA)
    agg = confirmadas.aggregate(n=Count('pk'), total=Sum('total'))
    hoy = timezone.localdate()
    inicio_mes = timezone.make_aware(datetime(hoy.year, hoy.month, 1))
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    return {
        'num_ventas': agg['n'] or 0,
        'ingresos': agg['total'] or Decimal('0'),
        'ingresos_mes': confirmadas.filter(fecha__gte=inicio_mes).aggregate(t=Sum('total'))['t'] or Decimal('0'),
        'ventas_hoy': confirmadas.filter(fecha__gte=inicio_dia).count(),
        'num_anuladas': qs.filter(estado=Venta.Estado.ANULADA).count(),
        'por_dia': _ventas_por_dia(confirmadas),
        'por_mes': _ventas_por_mes(confirmadas),
    }


def estadisticas_generales():
    ventas = Venta.objects.all()
    datos = _resumen_ventas(ventas)
    top = (DetalleVenta.objects.filter(venta__estado=Venta.Estado.CONFIRMADA)
           .values('producto__nombre').annotate(unidades=Sum('cantidad'), monto=Sum('subtotal'))
           .order_by('-unidades')[:5])
    datos.update({
        'total_productos': Producto.objects.activos().count(),
        'total_clientes': Cliente.objects.activos().count(),
        'stock_bajo': Producto.objects.activos().stock_bajo().order_by('stock')[:8],
        'num_stock_bajo': Producto.objects.activos().stock_bajo().count(),
        'recientes': ventas.select_related('cliente', 'vendedor')[:8],
        'top_productos': {
            'labels': [t['producto__nombre'] for t in top],
            'valores': [int(t['unidades']) for t in top],
        },
    })
    return datos


def estadisticas_vendedor(usuario):
    ventas = Venta.objects.filter(vendedor=usuario)
    datos = _resumen_ventas(ventas)
    datos.update({
        'total_productos': Producto.objects.activos().filter(stock__gt=0).count(),
        'total_clientes': Cliente.objects.activos().count(),
        'recientes': ventas.select_related('cliente', 'vendedor')[:8],
    })
    return datos
