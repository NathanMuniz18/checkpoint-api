from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import RegistroUsuarioSerializer, PerfilSerializer, TrocarSenhaSerializer,SolicitarRedefinicaoSenhaSerializer, RedefinirSenhaEmailSerializer


@extend_schema(
    summary="Registra um novo usuário",
    description="""
    Cria uma nova conta de usuário no Checkpoint.
    Qualquer visitante pode acessar este endpoint (não precisa de token).
    As senhas devem coincidir e o e-mail deve ser único.
    """,
    tags=["Usuários"],
    request=RegistroUsuarioSerializer,
    responses={
        201: OpenApiExample(
            "Sucesso",
            value={"mensagem": "Usuário registrado com sucesso!"},
        ),
        400: OpenApiExample(
            "Erro de validação",
            value={"password_confirm": ["As senhas informadas não coincidem."]},
        ),
    },
    examples=[
        OpenApiExample(
            "Exemplo de registro",
            value={
                "username": "jogador123",
                "email": "jogador@email.com",
                "password": "senha@123",
                "password_confirm": "senha@123",
            },
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_usuario(request):
    """
    Registra um novo usuário no sistema.

    Depende de:
    - RegistroUsuarioSerializer
    - User (Django Auth)
    - Persona (criado automaticamente)

    :param Request request: objeto HTTP com username, email, password e password_confirm
    :return: mensagem de sucesso ou erros de validação
    :rtype: JSON
    """
    # Passa os dados recebidos do frontend para o validador
    serializer = RegistroUsuarioSerializer(data=request.data)

    # Se os dados cumprirem todas as regras (senhas iguais, email único)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"mensagem": "Usuário registrado com sucesso!"},
            status=status.HTTP_201_CREATED
        )

    # Se falhar a validação, devolve a lista de erros em formato JSON
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Retorna o perfil do usuário logado",
    description="""
    Retorna os dados do perfil (Persona) do usuário autenticado.
    Requer token JWT válido no header Authorization.
    """,
    tags=["Usuários"],
    responses={
        200: PerfilSerializer,
        401: OpenApiExample(
            "Não autenticado",
            value={"detail": "As credenciais de autenticação não foram fornecidas."},
        ),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ver_perfil(request):
    """
    Retorna o perfil do usuário autenticado.

    :param Request request: objeto HTTP com token JWT
    :return: dados do perfil do usuário
    :rtype: JSON
    """
    # Acessa o perfil (Persona) vinculado ao usuário logado
    perfil = request.user.perfil
    serializer = PerfilSerializer(perfil)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Atualiza o perfil do usuário logado",
    description="""
    Atualiza bio e/ou foto do perfil do usuário autenticado.
    Requer token JWT válido no header Authorization.
    """,
    tags=["Usuários"],
    request=PerfilSerializer,
    responses={
        200: PerfilSerializer,
        400: OpenApiExample(
            "Dados inválidos",
            value={"foto": ["Informe uma URL válida."]},
        ),
    },
    examples=[
        OpenApiExample(
            "Exemplo de atualização",
            value={
                "bio": "Jogador casual, amo RPGs!",
                "foto": "https://exemplo.com/foto.jpg",
            },
            request_only=True,
        )
    ],
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def atualizar_perfil(request):
    """
    Atualiza o perfil do usuário autenticado.

    :param Request request: objeto HTTP com bio e/ou foto
    :return: perfil atualizado
    :rtype: JSON
    """
    # Acessa o perfil vinculado ao usuário logado
    perfil = request.user.perfil

    # partial=True permite atualizar só alguns campos (PATCH)
    serializer = PerfilSerializer(perfil, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Troca a senha do usuário logado",
    description="""
    Permite que o usuário autenticado altere sua senha.
    É necessário informar a senha atual e a nova senha (confirmada).
    Requer token JWT válido no header Authorization.
    """,
    tags=["Usuários"],
    request=TrocarSenhaSerializer,
    responses={
        200: OpenApiExample(
            "Sucesso",
            value={"mensagem": "Senha alterada com sucesso!"},
        ),
        400: OpenApiExample(
            "Senha atual incorreta",
            value={"senha_atual": ["Senha atual incorreta."]},
        ),
    },
    examples=[
        OpenApiExample(
            "Exemplo de troca de senha",
            value={
                "senha_atual": "senha@123",
                "nova_senha": "novaSenha@456",
                "nova_senha_confirm": "novaSenha@456",
            },
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trocar_senha(request):
    """
    Troca a senha do usuário autenticado.

    :param Request request: objeto HTTP com senha_atual, nova_senha e nova_senha_confirm
    :return: mensagem de sucesso ou erros de validação
    :rtype: JSON
    """
    serializer = TrocarSenhaSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        # Salva a nova senha de forma segura (com hash)
        request.user.set_password(serializer.validated_data['nova_senha'])
        request.user.save()
        return Response({"mensagem": "Senha alterada com sucesso!"}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Solicita recuperação de senha por e-mail",
    description="Gera o token de segurança do Django e simula o envio do e-mail com o link.",
    tags=["Usuários - Autenticação"],
    request=SolicitarRedefinicaoSenhaSerializer,
)
@api_view(['POST'])
@permission_classes([AllowAny])
def esqueci_senha(request):
    serializer = SolicitarRedefinicaoSenhaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"mensagem": "Se o e-mail for válido, enviaremos as instruções."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Redefine a senha via token de e-mail",
    description="Valida o uid e o token gerados pelo Django e aplica a nova senha informada.",
    tags=["Usuários - Autenticação"],
    request=RedefinirSenhaEmailSerializer,
)
@api_view(['POST'])
@permission_classes([AllowAny])
def redefinir_senha(request):
    serializer = RedefinirSenhaEmailSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"mensagem": "Sua senha foi redefinida com sucesso!"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)