import threading
import unittest
from decimal import Decimal

from django.db import connection, connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from core.testing import crear_admin, crear_cliente, crear_producto, crear_vendedor
from productos.models import Producto
from usuarios.roles import sincronizar_grupos
from ventas.models import DetalleVenta, Venta
from ventas.services import VentaError, anular_venta, registrar_venta


class RegistrarVentaTests(TestCase):
    def setUp(self):
        self.vendedor = crear_vendedor()
        self.cliente = crear_cliente()
        self.p1 = crear_producto('P1', precio='10.50', stock=5)
        self.p2 = crear_producto('P2', precio='3.33', stock=10)

    def test_venta_descuenta_stock_y_calcula_totales(self):
        venta = registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk,
                                items=[(self.p1.pk, 2), (self.p2.pk, 3)])
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertEqual((self.p1.stock, self.p2.stock), (3, 7))
        self.assertEqual(venta.subtotal, Decimal('30.99'))  # 21.00 + 9.99
        self.assertEqual(venta.total, Decimal('30.99'))
        self.assertEqual(venta.estado, Venta.Estado.CONFIRMADA)
        self.assertEqual(venta.vendedor, self.vendedor)
        self.assertEqual(venta.detalles.count(), 2)

    def test_productos_repetidos_se_consolidan(self):
        venta = registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk,
                                items=[(self.p1.pk, 2), (self.p1.pk, 1)])
        detalle = venta.detalles.get()
        self.assertEqual(detalle.cantidad, 3)

    def test_no_permite_superar_inventario_y_no_guarda_nada(self):
        with self.assertRaises(VentaError):
            registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk,
                            items=[(self.p2.pk, 1), (self.p1.pk, 6)])
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertEqual((self.p1.stock, self.p2.stock), (5, 10))
        self.assertFalse(Venta.objects.exists())

    def test_producto_inactivo_o_cliente_inactivo(self):
        self.p1.activo = False; self.p1.save()
        with self.assertRaises(VentaError):
            registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk, items=[(self.p1.pk, 1)])
        self.cliente.activo = False; self.cliente.save()
        with self.assertRaises(VentaError):
            registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk, items=[(self.p2.pk, 1)])

    def test_cantidad_cero_o_sin_items(self):
        with self.assertRaises(VentaError):
            registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk, items=[(self.p1.pk, 0)])
        with self.assertRaises(VentaError):
            registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk, items=[])

    def test_precio_historico_se_conserva(self):
        venta = registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk, items=[(self.p1.pk, 1)])
        self.p1.precio_venta = Decimal('99.00'); self.p1.save()
        detalle = venta.detalles.get()
        self.assertEqual(detalle.precio_unitario, Decimal('10.50'))
        venta.refresh_from_db()
        self.assertEqual(venta.total, Decimal('10.50'))


class AnularVentaTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.vendedor = crear_vendedor()
        self.cliente = crear_cliente()
        self.p1 = crear_producto('P1', stock=5)
        self.venta = registrar_venta(vendedor=self.vendedor, cliente_id=self.cliente.pk, items=[(self.p1.pk, 4)])

    def test_anular_restaura_inventario(self):
        anular_venta(venta_id=self.venta.pk, usuario=self.admin, motivo='Cliente devolvió todo')
        self.p1.refresh_from_db(); self.venta.refresh_from_db()
        self.assertEqual(self.p1.stock, 5)
        self.assertEqual(self.venta.estado, Venta.Estado.ANULADA)
        self.assertEqual(self.venta.anulada_por, self.admin)
        self.assertIsNotNone(self.venta.fecha_anulacion)

    def test_no_se_anula_dos_veces(self):
        anular_venta(venta_id=self.venta.pk, usuario=self.admin, motivo='Primer intento')
        with self.assertRaises(VentaError):
            anular_venta(venta_id=self.venta.pk, usuario=self.admin, motivo='Segundo intento')
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 5)  # no se duplicó la devolución

    def test_vendedor_no_puede_anular(self):
        with self.assertRaises(VentaError):
            anular_venta(venta_id=self.venta.pk, usuario=self.vendedor, motivo='Quiero anular')
        self.client.force_login(self.vendedor)
        resp = self.client.post(reverse('ventas:anular', args=[self.venta.pk]), {'motivo': 'Quiero anular'})
        self.assertEqual(resp.status_code, 403)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.estado, Venta.Estado.CONFIRMADA)

    def test_motivo_obligatorio(self):
        with self.assertRaises(VentaError):
            anular_venta(venta_id=self.venta.pk, usuario=self.admin, motivo='  ')

    def test_vista_anular_admin(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('ventas:anular', args=[self.venta.pk]), {'motivo': 'Error de digitación'})
        self.assertRedirects(resp, reverse('ventas:detalle', args=[self.venta.pk]))
        self.venta.refresh_from_db()
        self.assertTrue(self.venta.esta_anulada)


class VentaVistasTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.v1 = crear_vendedor('vendedor1')
        self.v2 = crear_vendedor('vendedor2')
        self.cliente = crear_cliente()
        self.p1 = crear_producto('P1', precio='20.00', stock=10)

    def _post_venta(self, **extra):
        datos = {
            'cliente': self.cliente.pk, 'observaciones': '',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1', 'items-MAX_NUM_FORMS': '50',
            'items-0-producto': self.p1.pk, 'items-0-cantidad': '2',
        }
        datos.update(extra)
        return self.client.post(reverse('ventas:crear'), datos)

    def test_vendedor_registra_venta_e_ignora_precios_del_cliente(self):
        self.client.force_login(self.v1)
        resp = self._post_venta(**{'items-0-precio_unitario': '0.01', 'total': '0.01', 'subtotal': '0.01'})
        venta = Venta.objects.get()
        self.assertRedirects(resp, reverse('ventas:detalle', args=[venta.pk]))
        self.assertEqual(venta.total, Decimal('40.00'))
        self.assertEqual(venta.vendedor, self.v1)

    def test_vista_rechaza_exceso_de_stock(self):
        self.client.force_login(self.v1)
        resp = self._post_venta(**{'items-0-cantidad': '11'})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Venta.objects.exists())
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 10)

    def test_vendedor_solo_ve_sus_ventas(self):
        venta_v2 = registrar_venta(vendedor=self.v2, cliente_id=self.cliente.pk, items=[(self.p1.pk, 1)])
        venta_v1 = registrar_venta(vendedor=self.v1, cliente_id=self.cliente.pk, items=[(self.p1.pk, 1)])
        self.client.force_login(self.v1)
        resp = self.client.get(reverse('ventas:lista'))
        self.assertEqual(list(resp.context['ventas']), [venta_v1])
        self.assertEqual(self.client.get(reverse('ventas:detalle', args=[venta_v2.pk])).status_code, 404)
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ventas:lista'))
        self.assertEqual(set(resp.context['ventas']), {venta_v1, venta_v2})

    def test_no_existen_rutas_de_edicion_o_borrado(self):
        venta = registrar_venta(vendedor=self.v1, cliente_id=self.cliente.pk, items=[(self.p1.pk, 1)])
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(f'/ventas/{venta.pk}/editar/').status_code, 404)
        self.assertEqual(self.client.get(f'/ventas/{venta.pk}/eliminar/').status_code, 404)

    def test_formulario_nueva_venta_renderiza(self):
        self.client.force_login(self.v1)
        resp = self.client.get(reverse('ventas:crear'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'items-TOTAL_FORMS')


@unittest.skipUnless(connection.vendor == 'mysql', 'La prueba de concurrencia requiere MySQL (SELECT ... FOR UPDATE).')
class ConcurrenciaVentasTests(TransactionTestCase):
    """Dos vendedores intentan vender a la vez la última unidad: solo uno debe lograrlo."""

    def setUp(self):
        sincronizar_grupos()  # TransactionTestCase vacía las tablas entre pruebas
        self.cliente = crear_cliente()
        self.producto = crear_producto('ULT', stock=1)
        self.vendedores = [crear_vendedor('va'), crear_vendedor('vb')]

    def test_ultima_unidad(self):
        resultados = []
        barrera = threading.Barrier(2)

        def vender(vendedor):
            try:
                barrera.wait()
                registrar_venta(vendedor=vendedor, cliente_id=self.cliente.pk, items=[(self.producto.pk, 1)])
                resultados.append('ok')
            except VentaError:
                resultados.append('sin_stock')
            finally:
                connections.close_all()

        hilos = [threading.Thread(target=vender, args=(v,)) for v in self.vendedores]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        self.assertEqual(sorted(resultados), ['ok', 'sin_stock'])
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(Venta.objects.count(), 1)
        self.assertEqual(DetalleVenta.objects.count(), 1)
