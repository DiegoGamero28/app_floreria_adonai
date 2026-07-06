from django import forms

from .models import Categoria, Cliente, Producto, Venta


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(widget, forms.Select):
                widget.attrs.update({'class': 'form-select'})
            elif isinstance(widget, forms.FileInput):
                widget.attrs.update({'class': 'form-control'})
            else:
                widget.attrs.update({'class': 'form-control'})

            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('rows', 3)


class CategoriaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']


class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'categoria',
            'descripcion',
            'precio',
            'stock',
            'stock_minimo',
            'imagen',
            'activo',
        ]
        labels = {
            'categoria': 'Categoría',
            'descripcion': 'Descripción',
            'stock_minimo': 'Stock mínimo',
            'activo': 'Activo',
        }


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'direccion', 'observaciones']
        labels = {
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
        }


class VentaInternaForm(BootstrapFormMixin, forms.Form):
    ESTADOS_INTERNOS = (
        (Venta.Estado.PENDIENTE, 'Pendiente'),
        (Venta.Estado.PAGADO, 'Pagado'),
    )

    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        required=False,
        empty_label='Venta sin cliente registrado',
        label='Cliente registrado',
    )
    nombre_cliente = forms.CharField(max_length=120, required=False, label='Nombre del cliente')
    telefono_cliente = forms.CharField(max_length=20, required=False, label='Teléfono')
    canal = forms.ChoiceField(choices=Venta.Canal.choices, initial=Venta.Canal.PRESENCIAL)
    metodo_pago = forms.ChoiceField(
        choices=Venta.MetodoPago.choices,
        initial=Venta.MetodoPago.EFECTIVO,
        label='Método de pago',
    )
    estado = forms.ChoiceField(choices=ESTADOS_INTERNOS, initial=Venta.Estado.PAGADO)
    producto = forms.ModelChoiceField(queryset=Producto.objects.none())
    cantidad = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.order_by('nombre')
        self.fields['producto'].queryset = Producto.objects.filter(activo=True).order_by('nombre')


class CompraPublicaForm(BootstrapFormMixin, forms.Form):
    cantidad = forms.IntegerField(min_value=1, initial=1)
    nombre_cliente = forms.CharField(
        max_length=120,
        required=False,
        label='Nombre',
        help_text='Opcional, pero recomendado para coordinar el pedido.',
    )
    telefono_cliente = forms.CharField(max_length=20, required=False, label='Teléfono')
    direccion = forms.CharField(max_length=220, required=False, label='Dirección')
    observaciones = forms.CharField(required=False, widget=forms.Textarea, label='Observaciones')


class CsvUploadForm(BootstrapFormMixin, forms.Form):
    archivo = forms.FileField(label='Archivo CSV')
