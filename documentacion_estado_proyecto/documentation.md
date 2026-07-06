# Documentación de estado del proyecto

## Estado actual

La aplicación Django monolítica de Florería Adonai incluye catálogo público, compra simulada con Yape y WhatsApp, inventario, clientes, ventas, importación CSV y panel interno.

## Cambios de la Iteración 1

- Se corrigieron tildes en textos visibles del frontend.
- Se ocultaron del navbar público las opciones internas: Dashboard, Productos, Clientes, Ventas e Importar CSV.
- Se protegieron las rutas internas con validación de usuario `staff` o `superuser`.
- Las rutas internas devuelven `acceso no autorizado` con HTTP 403 cuando el visitante no tiene sesión autorizada.
- Se centró el bloque principal de Inicio para mejorar la presentación visual.
- `seed_demo` ahora crea o actualiza el superusuario demo `admin / admin123`.
- README y reglas del proyecto fueron actualizados.

## Flujo de acceso interno

1. Ejecutar migraciones y datos demo.
2. Entrar a `http://127.0.0.1:8000/admin/`.
3. Iniciar sesión con `admin / admin123`.
4. Abrir el sitio público o ir a `/dashboard/`.
5. El navbar mostrará las opciones internas solo mientras la sesión autorizada esté activa.

## Verificación recomendada

```bash
python manage.py check
python manage.py test
python manage.py seed_demo
```
