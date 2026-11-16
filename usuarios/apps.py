from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsuariosConfig(AppConfig):
    name = 'usuarios'
    verbose_name = 'Usuarios'

    def ready(self):
        from . import signals

        # Se ejecuta tras cada migrate, cuando ya existen todos los permisos.
        post_migrate.connect(signals.crear_grupos_tras_migrar, dispatch_uid='usuarios_crear_grupos')
