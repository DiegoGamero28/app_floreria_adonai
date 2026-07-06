# Reglas del prototipo Florería Adonai

## Acceso

- Las páginas públicas son Inicio, Catálogo, compra directa y confirmación de pedido.
- Dashboard, Productos, Clientes, Ventas e Importar CSV son secciones internas.
- Las secciones internas solo se muestran en el navbar cuando el usuario autenticado es `is_staff` o `is_superuser`.
- Si un visitante intenta acceder directamente a una ruta interna, debe recibir `acceso no autorizado` con HTTP 403.
- No se implementa registro ni login propio; se usa la sesión del admin de Django.
- Para la demo local se puede usar `admin / admin123` después de ejecutar `python manage.py seed_demo`.

## Interfaz

- Los textos visibles al público deben usar tildes y redacción en español.
- El bloque principal de Inicio debe estar centrado y verse bien en laptop y celular.
- Las rutas técnicas y columnas CSV conservan sus nombres sin tildes: `catalogo`, `telefono`, `direccion`, `categoria`, `stock_minimo`.

## Negocio

- No se vende más cantidad que el stock disponible.
- Las ventas descuentan stock.
- Las ventas canceladas restauran stock.
- El catálogo público solo muestra productos activos.
