from django.urls import path
from . import views

urlpatterns = [
    # Registro de novo usuário (público)
    path('registrar/', views.registrar_usuario, name='registrar_usuario'),

    # Perfil do usuário logado (protegido)
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/atualizar/', views.atualizar_perfil, name='atualizar_perfil'),

    # Troca de senha (protegido)
    path('trocar-senha/', views.trocar_senha, name='trocar_senha'),
]