from django.views.generic import TemplateView

from .estadisticas import estadisticas_generales, estadisticas_vendedor


class DashboardView(TemplateView):
    """
    Panel principal (requiere sesión por LoginRequiredMiddleware).
    Con el permiso de estadísticas generales se ven los datos de toda la empresa;
    sin él, únicamente los del propio vendedor.
    """
    template_name = 'dashboard/inicio.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario = self.request.user
        generales = usuario.has_perm('ventas.ver_estadisticas_generales')
        ctx['vista_general'] = generales
        ctx['stats'] = estadisticas_generales() if generales else estadisticas_vendedor(usuario)
        return ctx
