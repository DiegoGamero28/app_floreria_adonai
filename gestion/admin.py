from django.contrib import admin

from .models import Categoria, Cliente, DetalleVenta, Producto, Venta


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'stock_bajo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')
    list_editable = ('precio', 'stock', 'stock_minimo', 'activo')

    @admin.display(boolean=True, description='Stock bajo')
    def stock_bajo(self, obj):
        return obj.stock_bajo


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion', 'fecha_registro')
    search_fields = ('nombre', 'telefono', 'direccion')


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente_visible', 'fecha', 'canal', 'metodo_pago', 'estado', 'total')
    list_filter = ('canal', 'metodo_pago', 'estado', 'fecha')
    search_fields = ('cliente__nombre', 'nombre_cliente', 'telefono_cliente')
    inlines = [DetalleVentaInline]
