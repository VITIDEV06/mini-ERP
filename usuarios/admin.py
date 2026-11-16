from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'rol', 'is_active', 'is_superuser')
    list_filter = ('rol', 'is_active', 'is_superuser')
    # Los grupos y permisos se derivan del rol (usuarios/roles.py), por eso no se editan aquí.
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Datos personales', {'fields': ('first_name', 'last_name', 'email')}),
        ('Rol y estado', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'rol', 'password1', 'password2')}),
    )
