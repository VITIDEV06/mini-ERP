from django import forms

from clientes.models import Cliente
from core.forms import BootstrapFormMixin
from productos.models import Producto


class ProductoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.codigo} · {obj.nombre} (stock: {obj.stock})'


class ClienteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.nombre_completo} — {obj.identificacion}'


class VentaForm(BootstrapFormMixin, forms.Form):
    cliente = ClienteChoiceField(queryset=Cliente.objects.none(), empty_label='Seleccione un cliente')
    observaciones = forms.CharField(max_length=255, required=False,
                                    widget=forms.TextInput(attrs={'placeholder': 'Opcional'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.activos().order_by('apellido', 'nombre')


class ItemVentaForm(BootstrapFormMixin, forms.Form):
    """Una línea de la venta. Solo se aceptan producto y cantidad: el precio lo pone el backend."""
    producto = ProductoChoiceField(queryset=Producto.objects.none(), empty_label='Seleccione un producto')
    cantidad = forms.IntegerField(min_value=1, max_value=100000, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.activos().filter(stock__gt=0).order_by('nombre')
        self.fields['cantidad'].widget.attrs.update({'min': 1})


class BaseItemFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        items = [f.cleaned_data for f in self.forms
                 if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
        if not items:
            raise forms.ValidationError('Agregue al menos un producto a la venta.')

    def items(self):
        """[(producto_id, cantidad), ...] de las filas válidas."""
        return [(f.cleaned_data['producto'].pk, f.cleaned_data['cantidad'])
                for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]


ItemVentaFormSet = forms.formset_factory(
    ItemVentaForm, formset=BaseItemFormSet, extra=0, min_num=1, validate_min=True,
    can_delete=True, max_num=50, validate_max=True,
)


class AnularVentaForm(BootstrapFormMixin, forms.Form):
    motivo = forms.CharField(min_length=5, max_length=255, label='Motivo de la anulación',
                             widget=forms.Textarea(attrs={'rows': 3}))
