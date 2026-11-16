from django.contrib import admin
from django.urls import include, path

from usuarios.views import LoginView, LogoutView

urlpatterns = [
    path('', include('dashboard.urls')),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('usuarios/', include('usuarios.urls')),
    path('productos/', include('productos.urls')),
    path('clientes/', include('clientes.urls')),
    path('ventas/', include('ventas.urls')),
    path('admin/', admin.site.urls),
]
