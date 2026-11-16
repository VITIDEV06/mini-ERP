from datetime import datetime, time

from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from core.mixins import FiltroOrdenMixin, PermisoRequeridoMixin
from productos.models import Producto

from .forms import AnularVentaForm, ItemVentaFormSet, VentaForm
from .models import Venta
from .services import VentaError, anular_venta, registrar_venta, ventas_visibles_para


def _parse_fecha(valor):
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


class VentaListView(PermisoRequeridoMixin, FiltroOrdenMixin, ListView):
    permission_required = 'ventas.view_venta'
    template_name = 'ventas/lista.html'
    context_object_name = 'ventas'
    paginate_by = 15
    campos_orden = {'numero': 'pk', 'fecha': 'fecha', 'cliente': 'cliente__apellido', 'total': 'total'}
    orden_defecto = '-fecha'

    def get_queryset(self):
        qs = ventas_visibles_para(self.request.user)
        g = self.request.GET
        q = g.get('q', '').strip()
        if q:
            filtro = Q(cliente__identificacion__icontains=q) | Q(cliente__nombre__icontains=q) \
                | Q(cliente__apellido__icontains=q)
            if q.upper().lstrip('V-').isdigit():
                filtro |= Q(pk=int(q.upper().lstrip('V-')))
            qs = qs.filter(filtro)
        if g.get('estado') in Venta.Estado.values:
            qs = qs.filter(estado=g['estado'])
        tz = timezone.get_current_timezone()
        desde, hasta = _parse_fecha(g.get('desde')), _parse_fecha(g.get('hasta'))
        if desde:
            qs = qs.filter(fecha__gte=datetime.combine(desde, time.min, tzinfo=tz))
        if hasta:
            qs = qs.filter(fecha__lte=datetime.combine(hasta, time.max, tzinfo=tz))
        if self.request.user.has_perm('ventas.ver_todas_ventas') and g.get('vendedor', '').isdigit():
            qs = qs.filter(vendedor_id=int(g['vendedor']))
        return qs.order_by(self.get_orden(), '-pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.object_list
        ctx['total_filtrado'] = qs.filter(estado=Venta.Estado.CONFIRMADA).aggregate(t=Sum('total'))['t'] or 0
        ctx['estados'] = Venta.Estado.choices
        if self.request.user.has_perm('ventas.ver_todas_ventas'):
            from usuarios.models import Usuario
            ctx['vendedores'] = Usuario.objects.filter(ventas__isnull=False).distinct().order_by('username')
        return ctx


class VentaDetailView(PermisoRequeridoMixin, DetailView):
    permission_required = 'ventas.view_venta'
    template_name = 'ventas/detalle.html'
    context_object_name = 'venta'

    def get_queryset(self):
        # Un vendedor que pida la venta de otro recibe 404.
        return ventas_visibles_para(self.request.user).select_related('anulada_por')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['detalles'] = self.object.detalles.select_related('producto')
        ctx['anular_form'] = AnularVentaForm()
        return ctx


class VentaCreateView(PermisoRequeridoMixin, View):
    permission_required = 'ventas.add_venta'
    template_name = 'ventas/form.html'

    def _contexto(self, form, formset):
        productos = Producto.objects.activos().filter(stock__gt=0).order_by('nombre')
        return {'form': form, 'formset': formset, 'productos': productos}

    def get(self, request):
        return render(request, self.template_name, self._contexto(VentaForm(), ItemVentaFormSet(prefix='items')))

    def post(self, request):
        form = VentaForm(request.POST)
        formset = ItemVentaFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            try:
                venta = registrar_venta(
                    vendedor=request.user,
                    cliente_id=form.cleaned_data['cliente'].pk,
                    items=formset.items(),
                    observaciones=form.cleaned_data['observaciones'],
                )
            except VentaError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                messages.success(request, f'Venta {venta.numero} registrada por un total de $ {venta.total:,.2f}.')
                return redirect('ventas:detalle', pk=venta.pk)
        return render(request, self.template_name, self._contexto(form, formset), status=400)


class VentaAnularView(PermisoRequeridoMixin, View):
    permission_required = 'ventas.anular_venta'
    http_method_names = ['post']

    def post(self, request, pk):
        venta = get_object_or_404(Venta, pk=pk)
        form = AnularVentaForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Indique un motivo de anulación válido (mínimo 5 caracteres).')
            return redirect('ventas:detalle', pk=venta.pk)
        try:
            anular_venta(venta_id=venta.pk, usuario=request.user, motivo=form.cleaned_data['motivo'])
        except VentaError as exc:
            for msg in exc.messages:
                messages.error(request, msg)
        else:
            messages.success(request, f'Venta {venta.numero} anulada. El inventario fue restaurado.')
        return redirect('ventas:detalle', pk=venta.pk)
