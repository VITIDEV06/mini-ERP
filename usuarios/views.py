from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView, UpdateView

from core.mixins import FiltroOrdenMixin, PermisoRequeridoMixin

from .forms import LoginForm, UsuarioCrearForm, UsuarioEditarForm, UsuarioPasswordForm
from .models import Usuario


class LoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


class UsuarioListView(PermisoRequeridoMixin, FiltroOrdenMixin, ListView):
    permission_required = 'usuarios.view_usuario'
    model = Usuario
    template_name = 'usuarios/lista.html'
    context_object_name = 'usuarios'
    paginate_by = 15
    campos_orden = {'username': 'username', 'nombre': 'first_name', 'rol': 'rol', 'ingreso': 'last_login'}
    orden_defecto = 'username'

    def get_queryset(self):
        qs = Usuario.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q)
                           | Q(last_name__icontains=q) | Q(email__icontains=q))
        rol = self.request.GET.get('rol')
        if rol in Usuario.Rol.values:
            qs = qs.filter(rol=rol)
        estado = self.request.GET.get('estado')
        if estado in ('activo', 'inactivo'):
            qs = qs.filter(is_active=(estado == 'activo'))
        return qs.order_by(self.get_orden())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = Usuario.Rol.choices
        return ctx


class UsuarioCreateView(PermisoRequeridoMixin, CreateView):
    permission_required = 'usuarios.add_usuario'
    model = Usuario
    form_class = UsuarioCrearForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuarios:lista')

    def form_valid(self, form):
        messages.success(self.request, f'Usuario "{form.instance.username}" creado correctamente.')
        return super().form_valid(form)


class UsuarioUpdateView(PermisoRequeridoMixin, UpdateView):
    permission_required = 'usuarios.change_usuario'
    model = Usuario
    form_class = UsuarioEditarForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('usuarios:lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['editor'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Usuario "{form.instance.username}" actualizado.')
        return super().form_valid(form)


class UsuarioPasswordView(PermisoRequeridoMixin, FormView):
    permission_required = 'usuarios.change_usuario'
    form_class = UsuarioPasswordForm
    template_name = 'usuarios/password.html'
    success_url = reverse_lazy('usuarios:lista')

    def dispatch(self, request, *args, **kwargs):
        self.usuario = get_object_or_404(Usuario, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.usuario
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['usuario_obj'] = self.usuario
        return ctx

    def form_valid(self, form):
        form.save()
        if self.usuario.pk == self.request.user.pk:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(self.request, self.usuario)
        messages.success(self.request, f'Contraseña de "{self.usuario.username}" actualizada.')
        return super().form_valid(form)


class UsuarioEstadoView(PermisoRequeridoMixin, View):
    """Activa / desactiva un usuario (solo POST)."""
    permission_required = 'usuarios.change_usuario'
    http_method_names = ['post']

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        if usuario.pk == request.user.pk:
            messages.error(request, 'No puedes desactivar tu propia cuenta.')
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=['is_active'])
            estado = 'activado' if usuario.is_active else 'desactivado'
            messages.success(request, f'Usuario "{usuario.username}" {estado}.')
        return redirect('usuarios:lista')
