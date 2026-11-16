from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.UsuarioListView.as_view(), name='lista'),
    path('nuevo/', views.UsuarioCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='editar'),
    path('<int:pk>/password/', views.UsuarioPasswordView.as_view(), name='password'),
    path('<int:pk>/estado/', views.UsuarioEstadoView.as_view(), name='estado'),
]
