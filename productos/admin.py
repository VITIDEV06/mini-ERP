from django.contrib import admin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio_venta', 'stock', 'stock_minimo', 'activo')
    list_filter = ('activo', 'categoria')
    search_fields = ('codigo', 'nombre')

    def has_delete_permission(self, request, obj=None):
        return False  # Los productos se desactivan, no se eliminan.
