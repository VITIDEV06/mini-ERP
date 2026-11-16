from django import forms

from core.forms import BootstrapFormMixin

from .models import Cliente


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ('identificacion', 'nombre', 'apellido', 'telefono', 'email', 'direccion', 'activo')

    def clean_identificacion(self):
        ident = self.cleaned_data['identificacion'].strip().upper()
        if Cliente.objects.filter(identificacion__iexact=ident).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un cliente con esta identificación.')
        return ident

    def clean_nombre(self):
        return self.cleaned_data['nombre'].strip()

    def clean_apellido(self):
        return self.cleaned_data['apellido'].strip()

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()
