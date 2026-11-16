from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from core.testing import PASSWORD, crear_admin, crear_vendedor
from usuarios.models import Usuario
from usuarios.roles import GRUPO_ADMINISTRADOR, GRUPO_VENDEDOR


class AutenticacionTests(TestCase):
    def setUp(self):
        self.vendedor = crear_vendedor()

    def test_anonimo_redirige_a_login(self):
        for url in ['dashboard:inicio', 'productos:lista', 'clientes:lista', 'ventas:lista', 'usuarios:lista']:
            resp = self.client.get(reverse(url))
            self.assertEqual(resp.status_code, 302, url)
            self.assertTrue(resp.url.startswith(reverse('login')), url)

    def test_login_correcto_redirige_al_dashboard(self):
        resp = self.client.post(reverse('login'), {'username': 'vendedor1', 'password': PASSWORD})
        self.assertRedirects(resp, reverse('dashboard:inicio'))

    def test_login_incorrecto_muestra_error(self):
        resp = self.client.post(reverse('login'), {'username': 'vendedor1', 'password': 'mala'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Usuario o contraseña incorrectos.')

    def test_usuario_inactivo_no_puede_ingresar(self):
        self.vendedor.is_active = False
        self.vendedor.save()
        resp = self.client.post(reverse('login'), {'username': 'vendedor1', 'password': PASSWORD})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_por_post(self):
        self.client.force_login(self.vendedor)
        resp = self.client.post(reverse('logout'))
        self.assertRedirects(resp, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RolesYPermisosTests(TestCase):
    def test_grupos_creados_con_permisos(self):
        admin = Group.objects.get(name=GRUPO_ADMINISTRADOR)
        vend = Group.objects.get(name=GRUPO_VENDEDOR)
        self.assertTrue(admin.permissions.filter(codename='anular_venta').exists())
        self.assertFalse(vend.permissions.filter(codename='anular_venta').exists())
        self.assertTrue(vend.permissions.filter(codename='add_venta').exists())

    def test_rol_asigna_grupo_y_permisos(self):
        v = crear_vendedor()
        a = crear_admin()
        self.assertEqual(list(v.groups.values_list('name', flat=True)), [GRUPO_VENDEDOR])
        self.assertTrue(v.has_perm('ventas.add_venta'))
        self.assertFalse(v.has_perm('productos.add_producto'))
        self.assertTrue(a.has_perm('productos.add_producto'))
        self.assertTrue(a.has_perm('usuarios.add_usuario'))

    def test_cambio_de_rol_actualiza_grupo(self):
        v = crear_vendedor()
        v.rol = Usuario.Rol.ADMINISTRADOR
        v.save()
        v = Usuario.objects.get(pk=v.pk)  # limpiar caché de permisos
        self.assertTrue(v.has_perm('usuarios.view_usuario'))

    def test_superusuario_siempre_administrador(self):
        su = Usuario.objects.create_superuser('root', 'r@x.com', PASSWORD)
        self.assertEqual(su.rol, Usuario.Rol.ADMINISTRADOR)

    def test_vendedor_no_accede_a_funciones_administrativas_por_url(self):
        v = crear_vendedor()
        self.client.force_login(v)
        urls = [
            reverse('usuarios:lista'), reverse('usuarios:crear'),
            reverse('productos:crear'), reverse('productos:categorias'),
            reverse('clientes:crear'),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_vendedor_no_puede_desactivar_usuarios_por_post(self):
        v = crear_vendedor()
        otro = crear_vendedor('vendedor2')
        self.client.force_login(v)
        resp = self.client.post(reverse('usuarios:estado', args=[otro.pk]))
        self.assertEqual(resp.status_code, 403)
        otro.refresh_from_db()
        self.assertTrue(otro.is_active)


class GestionUsuariosTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.client.force_login(self.admin)

    def test_admin_crea_vendedor(self):
        resp = self.client.post(reverse('usuarios:crear'), {
            'username': 'nuevo', 'first_name': 'Nuevo', 'last_name': 'Vendedor', 'email': 'n@x.com',
            'rol': 'VENDEDOR', 'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(resp, reverse('usuarios:lista'))
        u = Usuario.objects.get(username='nuevo')
        self.assertTrue(u.check_password(PASSWORD))
        self.assertTrue(u.groups.filter(name=GRUPO_VENDEDOR).exists())

    def test_admin_no_puede_desactivarse_a_si_mismo(self):
        self.client.post(reverse('usuarios:estado', args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_cambia_password(self):
        v = crear_vendedor()
        nueva = 'OtraClave#2026x'
        resp = self.client.post(reverse('usuarios:password', args=[v.pk]),
                                {'new_password1': nueva, 'new_password2': nueva})
        self.assertRedirects(resp, reverse('usuarios:lista'))
        v.refresh_from_db()
        self.assertTrue(v.check_password(nueva))
