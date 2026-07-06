from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Cliente, Producto, Venta
from .views import importar_clientes_csv, importar_productos_csv


class AccesoInternoTests(TestCase):
    def test_visitante_no_ve_enlaces_internos_y_recibe_403(self):
        catalogo = self.client.get(reverse('gestion:catalogo'))
        self.assertNotContains(catalogo, 'Dashboard')
        self.assertNotContains(catalogo, 'Importar CSV')

        response = self.client.get(reverse('gestion:dashboard'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(), 'acceso no autorizado')

    def test_superusuario_puede_ver_y_entrar_a_secciones_internas(self):
        User = get_user_model()
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
        )
        self.client.force_login(admin)

        catalogo = self.client.get(reverse('gestion:catalogo'))
        self.assertContains(catalogo, 'Dashboard')
        self.assertContains(catalogo, 'Importar CSV')

        response = self.client.get(reverse('gestion:dashboard'))
        self.assertEqual(response.status_code, 200)


class CompraPublicaTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Flores')
        self.producto = Producto.objects.create(
            nombre='Ramo de prueba',
            categoria=self.categoria,
            descripcion='Ramo para pruebas',
            precio=Decimal('25.00'),
            stock=5,
            stock_minimo=1,
        )

    def test_compra_publica_registra_venta_y_descuenta_stock(self):
        response = self.client.post(
            reverse('gestion:comprar_producto', args=[self.producto.pk]),
            {
                'cantidad': 2,
                'nombre_cliente': 'Ana',
                'telefono_cliente': '999888777',
                'direccion': 'Lima',
                'observaciones': 'Entregar por la tarde',
            },
        )

        venta = Venta.objects.get()
        self.assertRedirects(response, reverse('gestion:confirmacion_compra', args=[venta.pk]))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)
        self.assertEqual(venta.total, Decimal('50.00'))
        self.assertEqual(venta.canal, Venta.Canal.WEB)
        self.assertEqual(venta.metodo_pago, Venta.MetodoPago.YAPE)
        self.assertEqual(Cliente.objects.get(telefono='999888777').nombre, 'Ana')

    def test_compra_publica_no_permite_vender_mas_que_stock(self):
        response = self.client.post(
            reverse('gestion:comprar_producto', args=[self.producto.pk]),
            {'cantidad': 20, 'nombre_cliente': 'Ana', 'telefono_cliente': '999888777'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Venta.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)


class ImportacionCsvTests(TestCase):
    def test_importa_productos_creando_categoria_y_actualizando_por_nombre(self):
        contenido = (
            'nombre,categoria,descripcion,precio,stock,stock_minimo,activo\n'
            'Ramo CSV,Flores,Demo,30.50,7,2,true\n'
            'Ramo CSV,Flores,Actualizado,31.00,5,1,true\n'
        )
        archivo = SimpleUploadedFile('productos.csv', contenido.encode('utf-8'), content_type='text/csv')

        resumen = importar_productos_csv(archivo)

        self.assertEqual(resumen['creados'], 1)
        self.assertEqual(resumen['actualizados'], 1)
        producto = Producto.objects.get(nombre='Ramo CSV')
        self.assertEqual(producto.precio, Decimal('31.00'))
        self.assertEqual(producto.stock, 5)

    def test_importa_clientes_actualizando_por_telefono(self):
        contenido = (
            'nombre,telefono,direccion,observaciones\n'
            'Luis,999111222,Lima,Primera compra\n'
            'Luis Actualizado,999111222,Callao,Cliente frecuente\n'
        )
        archivo = SimpleUploadedFile('clientes.csv', contenido.encode('utf-8'), content_type='text/csv')

        resumen = importar_clientes_csv(archivo)

        self.assertEqual(resumen['creados'], 1)
        self.assertEqual(resumen['actualizados'], 1)
        cliente = Cliente.objects.get(telefono='999111222')
        self.assertEqual(cliente.nombre, 'Luis Actualizado')
        self.assertEqual(cliente.direccion, 'Callao')
