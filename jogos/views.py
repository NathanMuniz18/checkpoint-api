import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import Jogo, JogoUsuario
from .serializers import JogoUsuarioSerializer, JogoSerializer

RAWG_API_URL = "https://api.rawg.io/api/games"
RAWG_API_KEY = "f0b273f8e805432c9735cecf5c3648fd"


def _buscar_jogos_rawg(termo_busca):
    """
    Função auxiliar que busca jogos na API externa da RAWG.

    Baseada na lógica do T1 (checkpoint-site) com tratamento de erro robusto
    e extração de plataformas.

    :param str termo_busca: nome do jogo a buscar
    :return: lista de jogos e mensagem de erro (se houver)
    :rtype: tuple(list, str)
    """
    params = urlencode({
        "key": RAWG_API_KEY,
        "search": termo_busca,
        "page_size": 10,
    })
    url = f"{RAWG_API_URL}?{params}"

    try:
        with urlopen(url, timeout=8) as resposta:
            payload = json.loads(resposta.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError):
        return [], "Não foi possível consultar a RAWG agora. Tente novamente."

    jogos = []
    for item in payload.get("results", []):
        rawg_id = item.get("id")
        if not rawg_id:
            continue

        # Extrai até 3 plataformas do jogo (lógica melhorada do T1)
        plataformas = []
        for plataforma in item.get("platforms") or []:
            nome_plataforma = (plataforma.get("platform") or {}).get("name")
            if nome_plataforma:
                plataformas.append(nome_plataforma)

        jogos.append({
            "rawg_id": rawg_id,
            "nome": item.get("name", "Sem nome"),
            "capa_url": item.get("background_image") or "",
            "plataforma": ", ".join(plataformas[:3]),
            "slug": item.get("slug", ""),
        })

    return jogos, ""


@extend_schema(
    summary="Busca jogos na RAWG",
    description="""
    Busca jogos na API externa da RAWG pelo nome.
    Retorna até 10 resultados com id, nome, capa, plataformas e slug.
    Requer token JWT válido.
    """,
    tags=["Jogos"],
    parameters=[
        OpenApiParameter(
            name='q',
            description='Nome do jogo a buscar',
            type=str,
            required=True,
            examples=[
                OpenApiExample(
                    "Exemplo de busca",
                    value="God of War",
                )
            ]
        )
    ],
    responses={
        200: JogoSerializer(many=True),
        400: OpenApiExample(
            "Parâmetro ausente",
            value={"erro": "Envie o parâmetro 'q' na URL para buscar."},
        ),
        500: OpenApiExample(
            "Erro na RAWG",
            value={"erro": "Não foi possível consultar a RAWG agora. Tente novamente."},
        ),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_jogos_rawg(request):
    """
    Busca jogos na API externa da RAWG.

    Depende de:
    - _buscar_jogos_rawg (função auxiliar)
    - RAWG API (externa)

    :param Request request: objeto HTTP com parâmetro 'q' na query string
    :return: lista de jogos encontrados ou mensagem de erro
    :rtype: JSON
    """
    query = request.GET.get('q', '').strip()

    # Valida se o parâmetro de busca foi enviado
    if not query:
        return Response(
            {"erro": "Envie o parâmetro 'q' na URL para buscar."},
            status=status.HTTP_400_BAD_REQUEST
        )

    jogos, erro = _buscar_jogos_rawg(query)

    # Se houve erro na comunicação com a RAWG
    if erro:
        return Response({"erro": erro}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(jogos, status=status.HTTP_200_OK)


@extend_schema(
    summary="Lista a jornada do usuário",
    description="""
    Retorna todos os jogos da jornada do usuário autenticado.
    Cada usuário vê apenas os seus próprios jogos.
    Requer token JWT válido.
    """,
    tags=["Jornada"],
    responses={
        200: JogoUsuarioSerializer(many=True),
        401: OpenApiExample(
            "Não autenticado",
            value={"detail": "As credenciais de autenticação não foram fornecidas."},
        ),
    },
)
class JornadaListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar jogos na jornada do usuário.

    GET  → lista todos os jogos da jornada do usuário logado
    POST → adiciona um novo jogo à jornada

    Depende de:
    - JogoUsuarioSerializer
    - Jogo
    - JogoUsuario
    """
    serializer_class = JogoUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna apenas os jogos do usuário autenticado.

        :return: queryset filtrado pelo usuário logado
        :rtype: QuerySet
        """
        return JogoUsuario.objects.filter(usuario=self.request.user)

    @extend_schema(
        summary="Adiciona um jogo à jornada",
        description="""
        Adiciona um novo jogo à jornada do usuário autenticado.
        O jogo é buscado ou criado automaticamente pelo rawg_id.
        Requer token JWT válido.
        """,
        tags=["Jornada"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "rawg_id": {"type": "integer", "description": "ID do jogo na RAWG", "example": 58175},
                    "nome": {"type": "string", "description": "Nome do jogo", "example": "God of War"},
                    "capa_url": {"type": "string", "description": "URL da capa do jogo", "example": "https://media.rawg.io/..."},
                    "slug": {"type": "string", "description": "Slug do jogo na RAWG", "example": "god-of-war"},
                    "status": {"type": "string", "description": "Status do jogo", "example": "vou_jogar",
                               "enum": ["vou_jogar", "to_jogando", "ja_zerei", "desisti"]},
                    "horas_jogadas": {"type": "integer", "description": "Horas jogadas", "example": 0},
                },
                "required": ["rawg_id", "nome"],
            }
        },
        responses={
            201: JogoUsuarioSerializer,
            400: OpenApiExample(
                "Dados inválidos",
                value={"erro": "rawg_id e nome são obrigatórios"},
            ),
        },
        examples=[
            OpenApiExample(
                "Exemplo de adição",
                value={
                    "rawg_id": 58175,
                    "nome": "God of War",
                    "capa_url": "https://media.rawg.io/media/games/4be/god-of-war.jpg",
                    "slug": "god-of-war",
                    "status": "vou_jogar",
                    "horas_jogadas": 0,
                },
                request_only=True,
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        """
        Adiciona um novo jogo à jornada do usuário.

        Busca ou cria o jogo pelo rawg_id antes de criar a relação JogoUsuario.

        :param Request request: objeto HTTP com rawg_id, nome, capa_url, slug, status e horas_jogadas
        :return: jogo adicionado à jornada ou erro de validação
        :rtype: JSON
        """
        rawg_id = request.data.get('rawg_id')
        nome = request.data.get('nome')

        # Valida campos obrigatórios
        if not rawg_id or not nome:
            return Response(
                {"erro": "rawg_id e nome são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Busca ou cria o jogo no banco pelo rawg_id
        jogo_obj, created = Jogo.objects.get_or_create(
            rawg_id=rawg_id,
            defaults={
                'nome': nome,
                'capa_url': request.data.get('capa_url', ''),
                'slug': request.data.get('slug', ''),
                'plataforma': request.data.get('plataforma', ''),
            }
        )

        # Monta os dados para criar a relação JogoUsuario
        dados_jornada = {
            'jogo': jogo_obj.id,
            'status': request.data.get('status', 'vou_jogar'),
            'horas_jogadas': request.data.get('horas_jogadas', 0)
        }

        serializer = self.get_serializer(data=dados_jornada)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Detalhes de um jogo da jornada",
    description="""
    Retorna, atualiza ou remove um jogo específico da jornada do usuário.
    O usuário só pode acessar seus próprios jogos.
    Requer token JWT válido.
    """,
    tags=["Jornada"],
)
class JornadaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para ver, editar e deletar um jogo específico da jornada.

    GET    → retorna um jogo da jornada pelo id
    PUT    → atualiza todos os campos do jogo
    PATCH  → atualiza campos específicos do jogo
    DELETE → remove o jogo da jornada

    Depende de:
    - JogoUsuarioSerializer
    - JogoUsuario
    """
    serializer_class = JogoUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna apenas os jogos do usuário autenticado.
        Garante que um usuário não acesse jogos de outro usuário.

        :return: queryset filtrado pelo usuário logado
        :rtype: QuerySet
        """
        return JogoUsuario.objects.filter(usuario=self.request.user)