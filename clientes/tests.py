from django.test import TestCase
from django.urls import reverse

from clientes.forms import ClienteForm
from clientes.models import Cliente
from core.testing import crear_admin, crear_cliente, crear_vendedor


def datos_form(**extra):
    datos = {'identificacion': '0102030405', 'nombre': 'Luis', 'apellido': 'Gómez', 'telefono': '+593 99 123 4567',
             'email': 'LUIS@Correo.com', 'direccion': 'Av. Siempre Viva 123', 'activo': 'on'}
    datos.update(extra)
    return datos


class ClienteValidacionTests(TestCase):
    def test_identificacion_duplicada(self):
        crear_cliente(identificacion='ABC12345')
        form = ClienteForm(data=datos_form(identificacion='abc12345'))
        self.assertFalse(form.is_valid())
        self.assertIn('identificacion', form.errors)

    def test_formatos_invalidos(self):
        form = ClienteForm(data=datos_form(identificacion='12', telefono='abc', email='no-es-correo'))
        self.assertFalse(form.is_valid())
        for campo in ('identificacion', 'telefono', 'email'):
            self.assertIn(campo, form.errors)

    def test_normaliza_email(self):
        form = ClienteForm(data=datos_form())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().email, 'luis@correo.com')


class ClienteVistasTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.vendedor = crear_vendedor()
        self.c1 = crear_cliente('1111111111', nombre='María', apellido='López', telefono='0987654321')
        self.c2 = crear_cliente('2222222222', nombre='Pedro', apellido='Ruiz', telefono='0922334455', activo=False)

    def test_busqueda(self):
        self.client.force_login(self.admin)
        for q, esperado in [('1111', [self.c1]), ('Ruiz', [self.c2]), ('0987', [self.c1]), ('maría lópez', [self.c1])]:
            resp = self.client.get(reverse('clientes:lista'), {'q': q})
            self.assertEqual(list(resp.context['clientes']), esperado, q)

    def test_admin_crea_y_desactiva(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('clientes:crear'), datos_form())
        c = Cliente.objects.get(identificacion='0102030405')
        self.client.post(reverse('clientes:estado', args=[c.pk]))
        c.refresh_from_db()
        self.assertFalse(c.activo)

    def test_vendedor_consulta_pero_no_modifica(self):
        self.client.force_login(self.vendedor)
        resp = self.client.get(reverse('clientes:lista'))
        self.assertEqual(list(resp.context['clientes']), [self.c1])
        self.assertEqual(self.client.get(reverse('clientes:detalle', args=[self.c1.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('clientes:crear')).status_code, 403)
        self.assertEqual(self.client.get(reverse('clientes:editar', args=[self.c1.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('clientes:estado', args=[self.c1.pk])).status_code, 403)
