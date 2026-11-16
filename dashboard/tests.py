from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.testing import crear_admin, crear_cliente, crear_producto, crear_vendedor
from ventas.services import anular_venta, registrar_venta


class DashboardTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.v1 = crear_vendedor('vendedor1')
        self.v2 = crear_vendedor('vendedor2')
        cliente = crear_cliente()
        p = crear_producto('P1', precio='10.00', stock=50, stock_minimo=46)
        registrar_venta(vendedor=self.v1, cliente_id=cliente.pk, items=[(p.pk, 1)])
        registrar_venta(vendedor=self.v2, cliente_id=cliente.pk, items=[(p.pk, 3)])
        anulada = registrar_venta(vendedor=self.v2, cliente_id=cliente.pk, items=[(p.pk, 2)])
        anular_venta(venta_id=anulada.pk, usuario=self.admin, motivo='Prueba de anulación')

    def test_admin_ve_estadisticas_generales(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('dashboard:inicio'))
        stats = resp.context['stats']
        self.assertTrue(resp.context['vista_general'])
        self.assertEqual(stats['num_ventas'], 2)          # las anuladas no cuentan
        self.assertEqual(stats['ingresos'], Decimal('40.00'))
        self.assertEqual(stats['num_stock_bajo'], 1)       # stock final 46 <= mínimo 46
        self.assertEqual(sum(stats['por_dia']['valores']), 40.0)
        self.assertEqual(stats['top_productos']['valores'], [4])

    def test_vendedor_ve_solo_lo_suyo(self):
        self.client.force_login(self.v1)
        resp = self.client.get(reverse('dashboard:inicio'))
        stats = resp.context['stats']
        self.assertFalse(resp.context['vista_general'])
        self.assertEqual(stats['num_ventas'], 1)
        self.assertEqual(stats['ingresos'], Decimal('10.00'))
        self.assertNotIn('top_productos', stats)
        self.assertNotContains(resp, 'Stock bajo')
