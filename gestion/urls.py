from django.urls import path

from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('catalogo/comprar/<int:producto_id>/', views.comprar_producto, name='comprar_producto'),
    path('pedido/<int:venta_id>/confirmacion/', views.confirmacion_compra, name='confirmacion_compra'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('productos/', views.productos_lista, name='productos_lista'),
    path('productos/nuevo/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/desactivar/', views.producto_desactivar, name='producto_desactivar'),
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('clientes/nuevo/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('ventas/', views.ventas_lista, name='ventas_lista'),
    path('ventas/nueva/', views.venta_crear, name='venta_crear'),
    path('ventas/<int:pk>/', views.venta_detalle, name='venta_detalle'),
    path('ventas/<int:pk>/cancelar/', views.venta_cancelar, name='venta_cancelar'),
    path('importar-csv/', views.importar_csv, name='importar_csv'),
]
