from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegistroUsuarioSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(request=RegistroUsuarioSerializer)
@api_view(['POST'])
@permission_classes([AllowAny]) # Garante que qualquer visitante (não autenticado) possa criar uma conta
def registrar_usuario(request):
    """
    Endpoint para criar uma nova conta de utilizador no Checkpoint.
    """
    # Passa os dados recebidos do frontend para o validador
    serializer = RegistroUsuarioSerializer(data=request.data)
    
    # Se os dados cumprirem todas as regras (senhas iguais, email único)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"mensagem": "Utilizador registado com sucesso!"}, 
            status=status.HTTP_201_CREATED
        )
        
    # Se falhar a validação, devolve a lista de erros em formato JSON
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)