from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.mixins import FiltroOrdenMixin, PermisoRequeridoMixin

from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto


class ProductoVisibleMixin:
    """Quien no puede modificar productos (vendedor) solo consulta los activos."""

    def productos_visibles(self):
        qs = Producto.objects.select_related('categoria')
        if not self.request.user.has_perm('productos.change_producto'):
            qs = qs.filter(activo=True)
        return qs


class ProductoListView(PermisoRequeridoMixin, ProductoVisibleMixin, FiltroOrdenMixin, ListView):
    permission_required = 'productos.view_producto'
    template_name = 'productos/lista.html'
    context_object_name = 'productos'
    paginate_by = 15
    campos_orden = {
        'codigo': 'codigo', 'nombre': 'nombre', 'categoria': 'categoria__nombre',
        'precio': 'precio_venta', 'stock': 'stock', 'actualizado': 'actualizado',
    }
    orden_defecto = 'nombre'

    def get_queryset(self):
        qs = self.productos_visibles()
        g = self.request.GET
        q = g.get('q', '').strip()
        if q:
            qs = qs.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
        if g.get('categoria', '').isdigit():
            qs = qs.filter(categoria_id=int(g['categoria']))
        if g.get('estado') in ('activo', 'inactivo'):
            qs = qs.filter(activo=(g['estado'] == 'activo'))
        if g.get('stock') == 'bajo':
            qs = qs.stock_bajo()
        elif g.get('stock') == 'agotado':
            qs = qs.filter(stock=0)
        return qs.order_by(self.get_orden(), 'pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categorias'] = Categoria.objects.all()
        ctx['total_stock_bajo'] = self.productos_visibles().filter(activo=True).stock_bajo().count()
        return ctx


class ProductoDetailView(PermisoRequeridoMixin, ProductoVisibleMixin, DetailView):
    permission_required = 'productos.view_producto'
    template_name = 'productos/detalle.html'
    context_object_name = 'producto'

    def get_queryset(self):
        return self.productos_visibles()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.has_perm('ventas.ver_todas_ventas'):
            ctx['ultimas_ventas'] = (self.object.detalles_venta.select_related('venta', 'venta__cliente')
                                     .order_by('-venta__fecha')[:10])
        return ctx


class ProductoCreateView(PermisoRequeridoMixin, CreateView):
    permission_required = 'productos.add_producto'
    model = Producto
    form_class = ProductoForm
    template_name = 'productos/form.html'

    def form_valid(self, form):
        messages.success(self.request, f'Producto "{form.instance.nombre}" registrado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('productos:detalle', args=[self.object.pk])


class ProductoUpdateView(PermisoRequeridoMixin, UpdateView):
    permission_required = 'productos.change_producto'
    model = Producto
    form_class = ProductoForm
    template_name = 'productos/form.html'

    def form_valid(self, form):
        messages.success(self.request, f'Producto "{form.instance.nombre}" actualizado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('productos:detalle', args=[self.object.pk])


class ProductoEstadoView(PermisoRequeridoMixin, View):
    """Activa / desactiva un producto (solo POST). Los productos no se eliminan."""
    permission_required = 'productos.change_producto'
    http_method_names = ['post']

    def post(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        producto.activo = not producto.activo
        producto.save(update_fields=['activo', 'actualizado'])
        estado = 'activado' if producto.activo else 'desactivado'
        messages.success(request, f'Producto "{producto.nombre}" {estado}.')
        return redirect('productos:detalle', pk=producto.pk)


# --- Categorías ---

class CategoriaListView(PermisoRequeridoMixin, ListView):
    permission_required = 'productos.view_categoria'
    template_name = 'productos/categorias.html'
    context_object_name = 'categorias'

    def get_queryset(self):
        return Categoria.objects.annotate(num_productos=Count('productos'))


class CategoriaCreateView(PermisoRequeridoMixin, CreateView):
    permission_required = 'productos.add_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'productos/categoria_form.html'

    def get_success_url(self):
        return reverse('productos:categorias')

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.nombre}" creada.')
        return super().form_valid(form)


class CategoriaUpdateView(PermisoRequeridoMixin, UpdateView):
    permission_required = 'productos.change_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'productos/categoria_form.html'

    def get_success_url(self):
        return reverse('productos:categorias')

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.nombre}" actualizada.')
        return super().form_valid(form)
