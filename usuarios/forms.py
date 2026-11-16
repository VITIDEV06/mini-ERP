from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm

from core.forms import BootstrapFormMixin

from .models import Usuario


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está desactivada.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Usuario', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'placeholder': 'Contraseña'})


class UsuarioCrearForm(BootstrapFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'rol')


class UsuarioEditarForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'rol', 'is_active')
        labels = {'is_active': 'Activo'}

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        if self.instance.is_superuser:
            # El rol de un superusuario siempre es administrador.
            self.fields['rol'].disabled = True

    def clean(self):
        datos = super().clean()
        if self.editor and self.instance.pk == self.editor.pk:
            if datos.get('is_active') is False:
                self.add_error('is_active', 'No puedes desactivar tu propia cuenta.')
            if datos.get('rol') and datos['rol'] != self.instance.rol:
                self.add_error('rol', 'No puedes cambiar tu propio rol.')
        return datos


class UsuarioPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass
