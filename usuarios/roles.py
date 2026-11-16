"""
Definición de roles mediante grupos y permisos nativos de Django.

Cada rol se materializa como un Group con un conjunto de permisos.
Las vistas comprueban permisos (user.has_perm), nunca el nombre del rol,
de modo que un vendedor no puede acceder a funciones administrativas
aunque modifique la URL.
"""

from django.contrib.auth.models import Group, Permission

GRUPO_ADMINISTRADOR = 'Administrador'
GRUPO_VENDEDOR = 'Vendedor'

PERMISOS_POR_GRUPO = {
    GRUPO_ADMINISTRADOR: [
        # Usuarios
        'usuarios.view_usuario', 'usuarios.add_usuario', 'usuarios.change_usuario',
        # Productos y categorías
        'productos.view_producto', 'productos.add_producto', 'productos.change_producto',
        'productos.view_categoria', 'productos.add_categoria', 'productos.change_categoria',
        'productos.ver_costos',
        # Clientes
        'clientes.view_cliente', 'clientes.add_cliente', 'clientes.change_cliente',
        # Ventas
        'ventas.view_venta', 'ventas.add_venta', 'ventas.anular_venta', 'ventas.ver_todas_ventas',
        # Dashboard
        'ventas.ver_estadisticas_generales',
    ],
    GRUPO_VENDEDOR: [
        'productos.view_producto',
        'clientes.view_cliente',
        'ventas.view_venta', 'ventas.add_venta',
    ],
}

GRUPO_POR_ROL = {
    'ADMINISTRADOR': GRUPO_ADMINISTRADOR,
    'VENDEDOR': GRUPO_VENDEDOR,
}


def _buscar_permiso(etiqueta):
    app_label, codename = etiqueta.split('.')
    return Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()


def sincronizar_grupos():
    """Crea/actualiza los grupos con sus permisos. Es idempotente."""
    for nombre, etiquetas in PERMISOS_POR_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        permisos = [p for p in (_buscar_permiso(e) for e in etiquetas) if p is not None]
        grupo.permissions.set(permisos)


def asignar_grupo_por_rol(usuario):
    """Deja al usuario únicamente en el grupo correspondiente a su rol."""
    nombre = GRUPO_POR_ROL[usuario.rol]
    grupo, _ = Group.objects.get_or_create(name=nombre)
    usuario.groups.set([grupo])
