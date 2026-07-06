# Florería Adonai

Aplicación web monolítica en Django para un prototipo universitario de inventario, clientes, ventas, catálogo público y compra simulada con Yape y WhatsApp.

## Estructura principal

```txt
floreria_adonai/
  settings.py
  urls.py
gestion/
  models.py
  forms.py
  views.py
  urls.py
  admin.py
  management/commands/seed_demo.py
templates/gestion/
  base.html
  inicio.html
  catalogo.html
  comprar_producto.html
  confirmacion_compra.html
  dashboard.html
  productos_lista.html
  producto_form.html
  clientes_lista.html
  cliente_form.html
  cliente_detalle.html
  ventas_lista.html
  venta_form.html
  venta_detalle.html
  importar_csv.html
static/
  css/styles.css
  img/placeholder_producto.svg
  img/floral_banner.svg
  img/qr_yape.svg
```

## Ejecución local

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Datos demo opcionales:

```bash
python manage.py seed_demo
```

El comando `seed_demo` crea categorías, productos, un cliente de prueba y el superusuario demo:

```txt
usuario: admin
contraseña: admin123
```

Estas credenciales son solo para el prototipo local.

## Acceso público y acceso interno

El público solo debe ver:

- Inicio: `http://127.0.0.1:8000/`
- Catálogo público: `http://127.0.0.1:8000/catalogo/`
- Compra y confirmación del pedido.

Las rutas internas están ocultas del navbar para visitantes y protegidas por sesión de usuario staff/superuser:

- Dashboard: `http://127.0.0.1:8000/dashboard/`
- Productos: `http://127.0.0.1:8000/productos/`
- Clientes: `http://127.0.0.1:8000/clientes/`
- Ventas: `http://127.0.0.1:8000/ventas/`
- Importar CSV: `http://127.0.0.1:8000/importar-csv/`

Si un visitante intenta abrir una ruta interna, el sistema responde `acceso no autorizado` con estado HTTP 403.

Para entrar como dueña/administradora, inicia sesión en:

```txt
http://127.0.0.1:8000/admin/
```

Luego abre las rutas internas o vuelve al sitio; el navbar mostrará las opciones privadas.

## CSV soportados

Productos:

```csv
nombre,categoria,descripcion,precio,stock,stock_minimo,activo
```

Clientes:

```csv
nombre,telefono,direccion,observaciones
```

La importación de productos crea categorías automáticamente y actualiza productos existentes por nombre. La importación de clientes actualiza clientes existentes por teléfono.

## Configuración comercial

En `floreria_adonai/settings.py` puedes cambiar:

```python
FLORERIA_NOMBRE = 'Florería Adonai'
FLORERIA_YAPE = '999999999'
FLORERIA_WHATSAPP = '51999999999'
FLORERIA_PROMO = 'Arreglos florales, detalles y regalos listos para sorprender.'
FLORERIA_QR_YAPE_STATIC = 'img/qr_yape.svg'
```

El QR de Yape incluido es una imagen demo. Para usar uno real, coloca el archivo en `static/img/` y actualiza `FLORERIA_QR_YAPE_STATIC`.

## Verificación

```bash
python manage.py check
python manage.py test
```
