from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
    )
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    imagen = models.FileField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo


class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=220, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['telefono'],
                condition=~Q(telefono=''),
                name='cliente_telefono_unico_si_existe',
            )
        ]

    def __str__(self):
        return f'{self.nombre} ({self.telefono})' if self.telefono else self.nombre


class Venta(models.Model):
    class Canal(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        WEB = 'web', 'Web'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        YAPE = 'yape', 'Yape'
        PLIN = 'plin', 'Plin'
        TRANSFERENCIA = 'transferencia', 'Transferencia'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PAGADO = 'pagado', 'Pagado'
        CANCELADO = 'cancelado', 'Cancelado'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas',
    )
    nombre_cliente = models.CharField(max_length=120, blank=True)
    telefono_cliente = models.CharField(max_length=20, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.PRESENCIAL)
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'Venta #{self.pk} - S/ {self.total}'

    @property
    def cliente_visible(self):
        if self.cliente:
            return self.cliente.nombre
        return self.nombre_cliente or 'Cliente no registrado'

    def recalcular_total(self, guardar=True):
        total = sum((detalle.subtotal for detalle in self.detalles.all()), Decimal('0.00'))
        self.total = total
        if guardar:
            self.save(update_fields=['total'])
        return total


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_venta')
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'detalle de venta'
        verbose_name_plural = 'detalles de venta'

    def __str__(self):
        return f'{self.producto} x {self.cantidad}'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
