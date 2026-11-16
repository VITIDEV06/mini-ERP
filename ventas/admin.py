from django.contrib import admin

from .models import DetalleVenta, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    can_delete = False
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """Solo lectura: las ventas se registran y anulan desde la aplicación (ventas.services)."""
    list_display = ('numero', 'fecha', 'cliente', 'vendedor', 'total', 'estado')
    list_filter = ('estado', 'vendedor')
    search_fields = ('cliente__identificacion', 'cliente__nombre', 'cliente__apellido')
    inlines = [DetalleVentaInline]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
