from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from gestion.models import Categoria, Cliente, Producto


class Command(BaseCommand):
    help = 'Crea categorías, productos, clientes y usuario administrador de ejemplo.'

    def handle(self, *args, **options):
        categorias = {}
        for nombre in ['Flores', 'Peluches', 'Globos', 'Chocolates', 'Arreglos']:
            categoria, _ = Categoria.objects.get_or_create(nombre=nombre)
            categorias[nombre] = categoria

        nombres_anteriores = {
            'Arreglo romantico': 'Arreglo romántico',
            'Globo corazon': 'Globo corazón',
        }
        for anterior, corregido in nombres_anteriores.items():
            if not Producto.objects.filter(nombre=corregido).exists():
                Producto.objects.filter(nombre=anterior).update(nombre=corregido)

        productos = [
            ('Ramo primaveral', 'Flores', 'Rosas y flores de temporada en envoltura decorativa.', '65.00', 12, 3),
            ('Arreglo romántico', 'Arreglos', 'Arreglo floral para aniversarios y San Valentín.', '95.00', 8, 2),
            ('Globo corazón', 'Globos', 'Globo metalizado con mensaje especial.', '18.00', 25, 5),
            ('Peluche mediano', 'Peluches', 'Peluche suave para acompañar un arreglo floral.', '45.00', 10, 2),
            ('Caja de chocolates', 'Chocolates', 'Chocolates surtidos para regalo.', '38.00', 15, 4),
        ]
        for nombre, categoria, descripcion, precio, stock, stock_minimo in productos:
            Producto.objects.update_or_create(
                nombre=nombre,
                defaults={
                    'categoria': categorias[categoria],
                    'descripcion': descripcion,
                    'precio': Decimal(precio),
                    'stock': stock,
                    'stock_minimo': stock_minimo,
                    'activo': True,
                },
            )

        Cliente.objects.update_or_create(
            telefono='987654321',
            defaults={
                'nombre': 'Cliente Demo',
                'direccion': 'Lima',
                'observaciones': 'Cliente creado para pruebas del prototipo.',
            },
        )

        User = get_user_model()
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@floreria-adonai.local'},
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('admin123')
        admin_user.save()

        self.stdout.write(self.style.SUCCESS('Datos demo y usuario admin/admin123 creados o actualizados.'))
