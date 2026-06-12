from django.urls import path
from . import views

urlpatterns = [
    # 1. Rota para buscar jogos na internet (RAWG)
    path('busca/', views.buscar_jogos_rawg, name='buscar_jogos_rawg'),
    
    # 2. Rota para listar a sua jornada e adicionar um novo jogo nela
    path('jornada/', views.JornadaListCreateView.as_view(), name='jornada_list_create'),
    
    # 3. Rota para gerenciar um jogo específico da sua lista (editar status ou apagar)
    # O <int:pk> significa que a URL vai esperar um número (o ID da relação)
    path('jornada/<int:pk>/', views.JornadaDetailView.as_view(), name='jornada_detail'),
]