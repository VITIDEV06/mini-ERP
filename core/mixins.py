from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured


class PermisoRequeridoMixin(PermissionRequiredMixin):
    """
    Exige un permiso nativo de Django.

    - Usuario anónimo: redirección al login (lo cubre también LoginRequiredMiddleware).
    - Usuario autenticado sin permiso: HTTP 403, aunque escriba la URL a mano.
    """
    raise_exception = False


class FiltroOrdenMixin:
    """Ordenamiento seguro a partir de ?orden=campo, restringido a una lista blanca."""
    campos_orden = {}
    orden_defecto = None

    def get_orden(self):
        if self.orden_defecto is None:
            raise ImproperlyConfigured('Define orden_defecto.')
        orden = self.request.GET.get('orden', '')
        clave = orden.lstrip('-')
        if clave in self.campos_orden:
            campo = self.campos_orden[clave]
            return f'-{campo}' if orden.startswith('-') else campo
        return self.orden_defecto

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['orden_actual'] = self.request.GET.get('orden', '')
        return ctx
