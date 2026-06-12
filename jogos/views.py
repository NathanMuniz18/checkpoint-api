import requests
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Jogo, JogoUsuario
from .serializers import JogoUsuarioSerializer

@extend_schema(
    description="Busca jogos na API externa da RAWG",
    parameters=[OpenApiParameter(name='q', description='Nome do jogo', type=str)]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_jogos_rawg(request):
    query = request.GET.get('q', '')
    if not query:
        return Response({"erro": "Envie o parâmetro 'q' na URL para buscar."}, status=400)

    API_KEY = "f0b273f8e805432c9735cecf5c3648fd" 
    url = f"https://api.rawg.io/api/games?key={API_KEY}&search={query}&page_size=10"

    try:
        resposta = requests.get(url)
        dados = resposta.json()
        
        jogos_limpos = []
        for item in dados.get('results', []):
            jogos_limpos.append({
                "rawg_id": item.get('id'),
                "nome": item.get('name'),
                "capa_url": item.get('background_image'),
                "slug": item.get('slug')
            })
        return Response(jogos_limpos)
    except Exception as e:
        return Response({"erro": "Falha ao contactar a RAWG."}, status=500)

class JornadaListCreateView(generics.ListCreateAPIView):
    serializer_class = JogoUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JogoUsuario.objects.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        rawg_id = request.data.get('rawg_id')
        nome = request.data.get('nome')

        if not rawg_id or not nome:
            return Response({"erro": "rawg_id e nome são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)

        jogo_obj, created = Jogo.objects.get_or_create(
            rawg_id=rawg_id,
            defaults={
                'nome': nome,
                'capa_url': request.data.get('capa_url', ''),
                'slug': request.data.get('slug', '')
            }
        )

        dados_jornada = {
            'jogo': jogo_obj.id,
            'status': request.data.get('status', 'vou_jogar'),
            'horas_jogadas': request.data.get('horas_jogadas', 0)
        }

        serializer = self.get_serializer(data=dados_jornada)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class JornadaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JogoUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JogoUsuario.objects.filter(usuario=self.request.user)