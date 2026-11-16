from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.mixins import FiltroOrdenMixin, PermisoRequeridoMixin

from .forms import ClienteForm
from .models import Cliente


class ClienteVisibleMixin:
    """Quien no puede modificar clientes (vendedor) solo consulta los activos."""

    def clientes_visibles(self):
        qs = Cliente.objects.all()
        if not self.request.user.has_perm('clientes.change_cliente'):
            qs = qs.filter(activo=True)
        return qs


class ClienteListView(PermisoRequeridoMixin, ClienteVisibleMixin, FiltroOrdenMixin, ListView):
    permission_required = 'clientes.view_cliente'
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 15
    campos_orden = {'identificacion': 'identificacion', 'nombre': 'nombre', 'apellido': 'apellido',
                    'registro': 'fecha_registro'}
    orden_defecto = 'apellido'

    def get_queryset(self):
        qs = self.clientes_visibles()
        q = self.request.GET.get('q', '').strip()
        if q:
            filtro = Q(identificacion__icontains=q) | Q(telefono__icontains=q)
            for palabra in q.split():
                filtro |= Q(nombre__icontains=palabra) | Q(apellido__icontains=palabra)
            qs = qs.filter(filtro)
        estado = self.request.GET.get('estado')
        if estado in ('activo', 'inactivo'):
            qs = qs.filter(activo=(estado == 'activo'))
        return qs.order_by(self.get_orden(), 'pk')


class ClienteDetailView(PermisoRequeridoMixin, ClienteVisibleMixin, DetailView):
    permission_required = 'clientes.view_cliente'
    template_name = 'clientes/detalle.html'
    context_object_name = 'cliente'

    def get_queryset(self):
        return self.clientes_visibles()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ventas = self.object.ventas.select_related('vendedor').order_by('-fecha')
        if not self.request.user.has_perm('ventas.ver_todas_ventas'):
            ventas = ventas.filter(vendedor=self.request.user)
        ctx['ventas'] = ventas[:10]
        return ctx


class ClienteCreateView(PermisoRequeridoMixin, CreateView):
    permission_required = 'clientes.add_cliente'
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'

    def form_valid(self, form):
        messages.success(self.request, f'Cliente "{form.instance.nombre_completo}" registrado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clientes:detalle', args=[self.object.pk])


class ClienteUpdateView(PermisoRequeridoMixin, UpdateView):
    permission_required = 'clientes.change_cliente'
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'

    def form_valid(self, form):
        messages.success(self.request, f'Cliente "{form.instance.nombre_completo}" actualizado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clientes:detalle', args=[self.object.pk])


class ClienteEstadoView(PermisoRequeridoMixin, View):
    """Activa / desactiva un cliente (solo POST). Los clientes no se eliminan."""
    permission_required = 'clientes.change_cliente'
    http_method_names = ['post']

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        cliente.activo = not cliente.activo
        cliente.save(update_fields=['activo'])
        estado = 'activado' if cliente.activo else 'desactivado'
        messages.success(request, f'Cliente "{cliente.nombre_completo}" {estado}.')
        return redirect('clientes:detalle', pk=cliente.pk)
