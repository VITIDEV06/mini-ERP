from django import forms
from django.db.models import Q

from core.forms import BootstrapFormMixin

from .models import Categoria, Producto


class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = ('codigo', 'nombre', 'descripcion', 'categoria', 'precio_venta', 'costo',
                  'stock', 'stock_minimo', 'activo')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_venta': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'costo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filtro = Q(activo=True)
        if self.instance.pk and self.instance.categoria_id:
            filtro |= Q(pk=self.instance.categoria_id)  # conservar la categoría actual aunque esté inactiva
        self.fields['categoria'].queryset = Categoria.objects.filter(filtro)
        self.fields['categoria'].empty_label = 'Sin categoría'

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip().upper()
        if Producto.objects.filter(codigo__iexact=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un producto con este código.')
        return codigo

    def clean_nombre(self):
        return self.cleaned_data['nombre'].strip()


class CategoriaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion', 'activo')

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if Categoria.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe una categoría con este nombre.')
        return nombre
