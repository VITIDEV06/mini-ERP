from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Usuario
from .roles import asignar_grupo_por_rol, sincronizar_grupos


def crear_grupos_tras_migrar(sender, **kwargs):
    sincronizar_grupos()


@receiver(post_save, sender=Usuario)
def sincronizar_grupo_usuario(sender, instance, raw=False, **kwargs):
    if not raw:
        asignar_grupo_por_rol(instance)
