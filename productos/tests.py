from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from core.testing import crear_admin, crear_producto, crear_vendedor
from productos.forms import ProductoForm
from productos.models import Producto


def datos_form(**extra):
    datos = {'codigo': 'abc-1', 'nombre': 'Teclado', 'descripcion': '', 'categoria': '',
             'precio_venta': '25.50', 'costo': '15.00', 'stock': '10', 'stock_minimo': '3', 'activo': 'on'}
    datos.update(extra)
    return datos


class ProductoModeloTests(TestCase):
    def test_codigo_normalizado_y_unico(self):
        crear_producto(codigo=' p001 ')
        self.assertTrue(Producto.objects.filter(codigo='P001').exists())
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_producto(codigo='P001')

    def test_formulario_rechaza_codigo_duplicado_sin_importar_mayusculas(self):
        crear_producto(codigo='ABC-1')
        form = ProductoForm(data=datos_form(codigo='abc-1'))
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)

    def test_formulario_rechaza_valores_negativos(self):
        form = ProductoForm(data=datos_form(stock='-1', precio_venta='-5', costo='-1', stock_minimo='-2'))
        self.assertFalse(form.is_valid())
        for campo in ('stock', 'precio_venta', 'costo', 'stock_minimo'):
            self.assertIn(campo, form.errors)

    def test_stock_bajo(self):
        crear_producto(codigo='A', stock=2, stock_minimo=2)
        crear_producto(codigo='B', stock=10, stock_minimo=2)
        self.assertEqual(list(Producto.objects.stock_bajo().values_list('codigo', flat=True)), ['A'])


class ProductoVistasTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.vendedor = crear_vendedor()
        self.activo = crear_producto(codigo='ACT', nombre='Mouse óptico')
        self.inactivo = crear_producto(codigo='INA', nombre='Monitor viejo', activo=False)

    def test_admin_crea_producto(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('productos:crear'), datos_form())
        p = Producto.objects.get(codigo='ABC-1')
        self.assertRedirects(resp, reverse('productos:detalle', args=[p.pk]))

    def test_busqueda_por_codigo_o_nombre(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('productos:lista'), {'q': 'mouse'})
        self.assertEqual(list(resp.context['productos']), [self.activo])
        resp = self.client.get(reverse('productos:lista'), {'q': 'INA'})
        self.assertEqual(list(resp.context['productos']), [self.inactivo])

    def test_orden_invalido_no_rompe(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('productos:lista'), {'orden': 'costo;drop'})
        self.assertEqual(resp.status_code, 200)

    def test_vendedor_solo_ve_activos_y_sin_costo(self):
        self.client.force_login(self.vendedor)
        resp = self.client.get(reverse('productos:lista'))
        self.assertEqual(list(resp.context['productos']), [self.activo])
        self.assertEqual(self.client.get(reverse('productos:detalle', args=[self.inactivo.pk])).status_code, 404)
        resp = self.client.get(reverse('productos:detalle', args=[self.activo.pk]))
        self.assertNotContains(resp, 'Costo')

    def test_vendedor_no_puede_editar_ni_desactivar(self):
        self.client.force_login(self.vendedor)
        self.assertEqual(self.client.get(reverse('productos:editar', args=[self.activo.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('productos:estado', args=[self.activo.pk])).status_code, 403)

    def test_admin_desactiva_producto(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('productos:estado', args=[self.activo.pk]))
        self.activo.refresh_from_db()
        self.assertFalse(self.activo.activo)

    def test_desactivar_requiere_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('productos:estado', args=[self.activo.pk])).status_code, 405)
