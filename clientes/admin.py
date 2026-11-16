from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'nombre', 'apellido', 'telefono', 'email', 'activo', 'fecha_registro')
    list_filter = ('activo',)
    search_fields = ('identificacion', 'nombre', 'apellido', 'telefono')

    def has_delete_permission(self, request, obj=None):
        return False  # Los clientes se desactivan, no se eliminan.
