from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario del sistema. El rol determina el grupo de Django (y por tanto
    los permisos) al que pertenece; ver usuarios/roles.py.
    """

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
        VENDEDOR = 'VENDEDOR', 'Vendedor'

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.VENDEDOR)
    email = models.EmailField('correo electrónico', blank=True)

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['username']

    def save(self, *args, **kwargs):
        # Un superusuario siempre tiene rol de administrador.
        if self.is_superuser:
            self.rol = self.Rol.ADMINISTRADOR
        super().save(*args, **kwargs)

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_vendedor(self):
        return self.rol == self.Rol.VENDEDOR

    def __str__(self):
        return self.get_full_name() or self.username
