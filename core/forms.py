from django import forms


class BootstrapFormMixin:
    """Añade las clases de Bootstrap 5 a los widgets y marca los campos con error."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                clase = 'form-check-input'
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                clase = 'form-select'
            else:
                clase = 'form-control'
            actuales = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{actuales} {clase}'.strip()

    def full_clean(self):
        # Se marca tras validar (no en __init__) para no forzar la validación
        # antes de que las subclases configuren sus campos.
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                widget = self.fields[nombre].widget
                if 'is-invalid' not in widget.attrs.get('class', ''):
                    widget.attrs['class'] = f"{widget.attrs.get('class', '')} is-invalid".strip()
