from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def moneda(valor):
    """Formatea un importe: 1234.5 -> $ 1,234.50"""
    try:
        valor = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        return '$ 0.00'
    return f'$ {valor:,.2f}'


@register.filter
def decimal_js(valor):
    """Importe con punto decimal, para atributos data-* leídos por JavaScript."""
    try:
        return f'{Decimal(valor):.2f}'
    except (InvalidOperation, TypeError, ValueError):
        return '0.00'


@register.simple_tag(takes_context=True)
def orden_link(context, campo):
    """Devuelve el valor de ?orden= alternando asc/desc para el campo dado."""
    actual = context.get('orden_actual', '')
    return f'-{campo}' if actual == campo else campo


@register.simple_tag(takes_context=True)
def orden_icono(context, campo):
    actual = context.get('orden_actual', '')
    if actual == campo:
        return 'bi-sort-up'
    if actual == f'-{campo}':
        return 'bi-sort-down'
    return 'bi-arrow-down-up text-muted opacity-50'
