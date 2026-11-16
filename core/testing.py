"""Utilidades para las pruebas de todas las apps."""

from decimal import Decimal

from clientes.models import Cliente
from productos.models import Producto
from usuarios.models import Usuario

PASSWORD = 'ClaveSegura#2026'


def crear_usuario(username, rol=Usuario.Rol.VENDEDOR, **extra):
    return Usuario.objects.create_user(username=username, password=PASSWORD, rol=rol, **extra)


def crear_admin(username='admin1'):
    return crear_usuario(username, rol=Usuario.Rol.ADMINISTRADOR)


def crear_vendedor(username='vendedor1'):
    return crear_usuario(username, rol=Usuario.Rol.VENDEDOR)


def crear_producto(codigo='P001', precio='10.00', stock=10, stock_minimo=2, **extra):
    datos = dict(codigo=codigo, nombre=f'Producto {codigo}', precio_venta=Decimal(precio),
                 costo=Decimal('5.00'), stock=stock, stock_minimo=stock_minimo)
    datos.update(extra)
    return Producto.objects.create(**datos)


def crear_cliente(identificacion='1712345678', **extra):
    datos = dict(identificacion=identificacion, nombre='Ana', apellido='Pérez', telefono='0991234567')
    datos.update(extra)
    return Cliente.objects.create(**datos)
