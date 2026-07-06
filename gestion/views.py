import csv
from functools import wraps
from decimal import Decimal, InvalidOperation
from io import StringIO
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ClienteForm, CompraPublicaForm, CsvUploadForm, ProductoForm, VentaInternaForm
from .models import Categoria, Cliente, DetalleVenta, Producto, Venta


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return view_func(request, *args, **kwargs)
        return HttpResponse('acceso no autorizado', status=403)

    return _wrapped_view


def inicio(request):
    categorias = Categoria.objects.filter(productos__activo=True).distinct()[:8]
    destacados = Producto.objects.filter(activo=True, stock__gt=0).select_related('categoria')[:6]
    return render(
        request,
        'gestion/inicio.html',
        {'categorias': categorias, 'destacados': destacados},
    )


def catalogo(request):
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query)
            | Q(categoria__nombre__icontains=query)
            | Q(descripcion__icontains=query)
        )
    return render(request, 'gestion/catalogo.html', {'productos': productos, 'query': query})


def comprar_producto(request, producto_id):
    producto = get_object_or_404(Producto.objects.select_related('categoria'), pk=producto_id, activo=True)
    cantidad_inicial = request.GET.get('cantidad') or 1

    if request.method == 'POST':
        form = CompraPublicaForm(request.POST)
        if form.is_valid():
            venta = _crear_venta_publica_si_hay_stock(form, producto)
            if venta:
                messages.success(request, 'Pedido registrado. Coordina la confirmación por WhatsApp.')
                return redirect('gestion:confirmacion_compra', venta_id=venta.pk)
    else:
        form = CompraPublicaForm(initial={'cantidad': cantidad_inicial})

    return render(request, 'gestion/comprar_producto.html', {'producto': producto, 'form': form})


def confirmacion_compra(request, venta_id):
    venta = get_object_or_404(
        Venta.objects.prefetch_related('detalles__producto').select_related('cliente'),
        pk=venta_id,
    )
    return render(
        request,
        'gestion/confirmacion_compra.html',
        {'venta': venta, 'whatsapp_url': _whatsapp_url_para_venta(venta)},
    )


@staff_required
def dashboard(request):
    ventas_validas = Venta.objects.exclude(estado=Venta.Estado.CANCELADO)
    total_vendido = ventas_validas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    context = {
        'total_productos': Producto.objects.count(),
        'total_clientes': Cliente.objects.count(),
        'total_ventas': Venta.objects.count(),
        'total_vendido': total_vendido,
        'productos_stock_bajo': Producto.objects.filter(stock__lte=F('stock_minimo')).select_related('categoria')[:10],
        'ventas_recientes': Venta.objects.select_related('cliente').prefetch_related('detalles')[:8],
    }
    return render(request, 'gestion/dashboard.html', context)


@staff_required
def productos_lista(request):
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.select_related('categoria')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query)
            | Q(categoria__nombre__icontains=query)
            | Q(descripcion__icontains=query)
        )
    return render(request, 'gestion/productos_lista.html', {'productos': productos, 'query': query})


@staff_required
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado correctamente.')
            return redirect('gestion:productos_lista')
    else:
        form = ProductoForm()
    return render(request, 'gestion/producto_form.html', {'form': form, 'titulo': 'Nuevo producto'})


@staff_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('gestion:productos_lista')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'gestion/producto_form.html', {'form': form, 'titulo': 'Editar producto'})


@staff_required
@require_POST
def producto_desactivar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = False
    producto.save(update_fields=['activo'])
    messages.info(request, f'Producto "{producto.nombre}" desactivado.')
    return redirect('gestion:productos_lista')


@staff_required
def clientes_lista(request):
    query = request.GET.get('q', '').strip()
    clientes = Cliente.objects.all()
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query)
            | Q(telefono__icontains=query)
            | Q(direccion__icontains=query)
        )
    return render(request, 'gestion/clientes_lista.html', {'clientes': clientes, 'query': query})


@staff_required
def cliente_crear(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado correctamente.')
            return redirect('gestion:clientes_lista')
    else:
        form = ClienteForm()
    return render(request, 'gestion/cliente_form.html', {'form': form, 'titulo': 'Nuevo cliente'})


@staff_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('gestion:cliente_detalle', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'gestion/cliente_form.html', {'form': form, 'titulo': 'Editar cliente'})


@staff_required
def cliente_detalle(request, pk):
    cliente = get_object_or_404(
        Cliente.objects.prefetch_related('ventas__detalles__producto'),
        pk=pk,
    )
    return render(request, 'gestion/cliente_detalle.html', {'cliente': cliente})


@staff_required
def ventas_lista(request):
    fecha = request.GET.get('fecha', '').strip()
    ventas = Venta.objects.select_related('cliente').prefetch_related('detalles__producto')
    if fecha:
        ventas = ventas.filter(fecha__date=fecha)
    return render(request, 'gestion/ventas_lista.html', {'ventas': ventas, 'fecha': fecha})


@staff_required
def venta_crear(request):
    if request.method == 'POST':
        form = VentaInternaForm(request.POST)
        if form.is_valid():
            venta = _crear_venta_interna_si_hay_stock(form)
            if venta:
                messages.success(request, 'Venta registrada y stock descontado.')
                return redirect('gestion:venta_detalle', pk=venta.pk)
    else:
        form = VentaInternaForm()
    return render(request, 'gestion/venta_form.html', {'form': form})


@staff_required
def venta_detalle(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related('cliente').prefetch_related('detalles__producto'),
        pk=pk,
    )
    return render(request, 'gestion/venta_detalle.html', {'venta': venta})


@staff_required
@require_POST
def venta_cancelar(request, pk):
    venta = get_object_or_404(Venta.objects.prefetch_related('detalles__producto'), pk=pk)
    if venta.estado == Venta.Estado.CANCELADO:
        messages.info(request, 'La venta ya estaba cancelada.')
        return redirect('gestion:venta_detalle', pk=venta.pk)

    with transaction.atomic():
        venta = Venta.objects.select_for_update().get(pk=pk)
        for detalle in venta.detalles.select_related('producto'):
            producto = detalle.producto
            producto.stock += detalle.cantidad
            producto.save(update_fields=['stock'])
        venta.estado = Venta.Estado.CANCELADO
        venta.save(update_fields=['estado'])
    messages.warning(request, 'Venta cancelada y stock restaurado.')
    return redirect('gestion:venta_detalle', pk=venta.pk)


@staff_required
def importar_csv(request):
    resumen = None
    producto_form = CsvUploadForm(prefix='productos')
    cliente_form = CsvUploadForm(prefix='clientes')

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        if tipo == 'productos':
            producto_form = CsvUploadForm(request.POST, request.FILES, prefix='productos')
            if producto_form.is_valid():
                resumen = importar_productos_csv(producto_form.cleaned_data['archivo'])
        elif tipo == 'clientes':
            cliente_form = CsvUploadForm(request.POST, request.FILES, prefix='clientes')
            if cliente_form.is_valid():
                resumen = importar_clientes_csv(cliente_form.cleaned_data['archivo'])

    return render(
        request,
        'gestion/importar_csv.html',
        {
            'producto_form': producto_form,
            'cliente_form': cliente_form,
            'resumen': resumen,
        },
    )


def importar_productos_csv(archivo):
    requeridas = ['nombre', 'categoria', 'descripcion', 'precio', 'stock', 'stock_minimo', 'activo']
    reader, errores = _reader_csv(archivo, requeridas)
    creados = actualizados = 0

    if errores:
        return {'tipo': 'productos', 'creados': 0, 'actualizados': 0, 'errores': errores}

    for numero_fila, row in enumerate(reader, start=2):
        try:
            nombre = (row.get('nombre') or '').strip()
            categoria_nombre = (row.get('categoria') or '').strip()
            if not nombre:
                raise ValueError('El nombre es obligatorio.')
            if not categoria_nombre:
                raise ValueError('La categoría es obligatoria.')

            categoria = _obtener_categoria(categoria_nombre)
            precio = _decimal_desde_csv(row.get('precio'))
            stock = _entero_desde_csv(row.get('stock'), 'stock')
            stock_minimo = _entero_desde_csv(row.get('stock_minimo'), 'stock_minimo')
            activo = _booleano_desde_csv(row.get('activo'))
            producto, creado = Producto.objects.update_or_create(
                nombre=nombre,
                defaults={
                    'categoria': categoria,
                    'descripcion': (row.get('descripcion') or '').strip(),
                    'precio': precio,
                    'stock': stock,
                    'stock_minimo': stock_minimo,
                    'activo': activo,
                },
            )
            creados += 1 if creado else 0
            actualizados += 0 if creado else 1
        except (ValueError, InvalidOperation) as exc:
            errores.append(f'Fila {numero_fila}: {exc}')

    return {'tipo': 'productos', 'creados': creados, 'actualizados': actualizados, 'errores': errores}


def importar_clientes_csv(archivo):
    requeridas = ['nombre', 'telefono', 'direccion', 'observaciones']
    reader, errores = _reader_csv(archivo, requeridas)
    creados = actualizados = 0

    if errores:
        return {'tipo': 'clientes', 'creados': 0, 'actualizados': 0, 'errores': errores}

    for numero_fila, row in enumerate(reader, start=2):
        try:
            nombre = (row.get('nombre') or '').strip()
            telefono = (row.get('telefono') or '').strip()
            if not nombre:
                raise ValueError('El nombre es obligatorio.')
            if not telefono:
                raise ValueError('El teléfono es obligatorio.')

            cliente = Cliente.objects.filter(telefono=telefono).first()
            datos = {
                'nombre': nombre,
                'direccion': (row.get('direccion') or '').strip(),
                'observaciones': (row.get('observaciones') or '').strip(),
            }
            if cliente:
                for campo, valor in datos.items():
                    setattr(cliente, campo, valor)
                cliente.save(update_fields=list(datos.keys()))
                actualizados += 1
            else:
                Cliente.objects.create(telefono=telefono, **datos)
                creados += 1
        except ValueError as exc:
            errores.append(f'Fila {numero_fila}: {exc}')

    return {'tipo': 'clientes', 'creados': creados, 'actualizados': actualizados, 'errores': errores}


def _reader_csv(archivo, columnas_requeridas):
    contenido = archivo.read().decode('utf-8-sig')
    reader = csv.DictReader(StringIO(contenido))
    fieldnames = reader.fieldnames or []
    faltantes = [columna for columna in columnas_requeridas if columna not in fieldnames]
    if faltantes:
        return [], [f'Faltan columnas obligatorias: {", ".join(faltantes)}']
    return reader, []


def _obtener_categoria(nombre):
    categoria = Categoria.objects.filter(nombre__iexact=nombre).first()
    if categoria:
        return categoria
    return Categoria.objects.create(nombre=nombre)


def _decimal_desde_csv(valor):
    texto = (valor or '').strip().replace(',', '.')
    if not texto:
        raise ValueError('El precio es obligatorio.')
    precio = Decimal(texto)
    if precio < 0:
        raise ValueError('El precio no puede ser negativo.')
    return precio


def _entero_desde_csv(valor, campo):
    texto = (valor or '').strip()
    if not texto:
        raise ValueError(f'El campo {campo} es obligatorio.')
    numero = int(texto)
    if numero < 0:
        raise ValueError(f'El campo {campo} no puede ser negativo.')
    return numero


def _booleano_desde_csv(valor):
    texto = (valor or '').strip().lower()
    if texto in ('1', 'true', 'si', 'sí', 'yes', 'activo', 'activa'):
        return True
    if texto in ('0', 'false', 'no', 'inactivo', 'inactiva'):
        return False
    return True


def _crear_o_actualizar_cliente(nombre, telefono, direccion='', observaciones=''):
    nombre = (nombre or '').strip()
    telefono = (telefono or '').strip()
    if not nombre and not telefono:
        return None

    if telefono:
        cliente = Cliente.objects.filter(telefono=telefono).first()
        if cliente:
            cliente.nombre = nombre or cliente.nombre
            cliente.direccion = direccion or cliente.direccion
            cliente.observaciones = observaciones or cliente.observaciones
            cliente.save(update_fields=['nombre', 'direccion', 'observaciones'])
            return cliente
        return Cliente.objects.create(
            nombre=nombre or 'Cliente web',
            telefono=telefono,
            direccion=direccion,
            observaciones=observaciones,
        )

    return Cliente.objects.create(nombre=nombre, direccion=direccion, observaciones=observaciones)


def _crear_venta_publica_si_hay_stock(form, producto_base):
    cantidad = form.cleaned_data['cantidad']
    with transaction.atomic():
        producto = Producto.objects.select_for_update().get(pk=producto_base.pk)
        if cantidad > producto.stock:
            form.add_error('cantidad', f'Solo hay {producto.stock} unidades disponibles.')
            return None

        cliente = _crear_o_actualizar_cliente(
            form.cleaned_data.get('nombre_cliente'),
            form.cleaned_data.get('telefono_cliente'),
            form.cleaned_data.get('direccion'),
            form.cleaned_data.get('observaciones'),
        )
        venta = Venta.objects.create(
            cliente=cliente,
            nombre_cliente=form.cleaned_data.get('nombre_cliente', ''),
            telefono_cliente=form.cleaned_data.get('telefono_cliente', ''),
            canal=Venta.Canal.WEB,
            metodo_pago=Venta.MetodoPago.YAPE,
            estado=Venta.Estado.PENDIENTE,
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio,
        )
        producto.stock -= cantidad
        producto.save(update_fields=['stock'])
        venta.recalcular_total()
        return venta


def _crear_venta_interna_si_hay_stock(form):
    cantidad = form.cleaned_data['cantidad']
    producto_form = form.cleaned_data['producto']
    with transaction.atomic():
        producto = Producto.objects.select_for_update().get(pk=producto_form.pk)
        if cantidad > producto.stock:
            form.add_error('cantidad', f'Solo hay {producto.stock} unidades disponibles.')
            return None

        cliente = form.cleaned_data.get('cliente')
        nombre = form.cleaned_data.get('nombre_cliente', '').strip()
        telefono = form.cleaned_data.get('telefono_cliente', '').strip()
        if not cliente and (nombre or telefono):
            cliente = _crear_o_actualizar_cliente(nombre, telefono)

        venta = Venta.objects.create(
            cliente=cliente,
            nombre_cliente=nombre or (cliente.nombre if cliente else ''),
            telefono_cliente=telefono or (cliente.telefono if cliente else ''),
            canal=form.cleaned_data['canal'],
            metodo_pago=form.cleaned_data['metodo_pago'],
            estado=form.cleaned_data['estado'],
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio,
        )
        producto.stock -= cantidad
        producto.save(update_fields=['stock'])
        venta.recalcular_total()
        return venta


def _whatsapp_url_para_venta(venta):
    detalles = list(venta.detalles.select_related('producto'))
    resumen = ', '.join(f'{d.producto.nombre} x {d.cantidad}' for d in detalles)
    cliente = venta.cliente_visible
    texto = (
        f'Hola, deseo confirmar mi pedido de Florería Adonai. '
        f'Cliente: {cliente}. Pedido: {resumen}. Total: S/ {venta.total}.'
    )
    return f'https://wa.me/{settings.FLORERIA_WHATSAPP}?text={quote(texto)}'
