from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Persona
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novos usuários.

    Valida que as senhas coincidem e que o email é único.
    Cria automaticamente um perfil (Persona) em branco para o novo usuário.
    """
    # Campos de senha definidos manualmente (write_only = nunca aparecem na resposta)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, data):
        """
        Valida os dados do registro.

        :param dict data: dados enviados pelo frontend
        :return: dados validados
        :raises ValidationError: se senhas não coincidem ou email já existe
        """
        # Confere se as senhas são iguais
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "As senhas informadas não coincidem."})

        # Confere se o email já está em uso no banco
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "Este endereço de e-mail já está cadastrado."})

        return data

    def create(self, validated_data):
        """
        Cria o usuário e seu perfil (Persona) automaticamente.

        :param dict validated_data: dados já validados
        :return: usuário criado
        :rtype: User
        """
        # Remove a confirmação de senha (não se salva no banco)
        validated_data.pop('password_confirm')

        # Cria o usuário criptografando a senha de forma segura
        usuario = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

        # Cria automaticamente o perfil Persona em branco para esse usuário
        Persona.objects.create(usuario=usuario)

        return usuario


class PerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para leitura e atualização do perfil (Persona) do usuário.
    """
    # Campos somente leitura vindos do User relacionado
    username = serializers.CharField(source='usuario.username', read_only=True)
    email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = Persona
        fields = ['id', 'username', 'email', 'bio', 'foto', 'criado_em']
        read_only_fields = ['id', 'username', 'email', 'criado_em']


class TrocarSenhaSerializer(serializers.Serializer):
    """
    Serializer para troca de senha do usuário autenticado.

    Valida que a senha atual está correta e que a nova senha é confirmada.
    """
    senha_atual = serializers.CharField(write_only=True)
    nova_senha = serializers.CharField(write_only=True)
    nova_senha_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Valida a senha atual e confirma a nova senha.

        :param dict data: dados enviados pelo frontend
        :return: dados validados
        :raises ValidationError: se senha atual incorreta ou novas senhas não coincidem
        """
        usuario = self.context['request'].user

        # Verifica se a senha atual está correta
        if not usuario.check_password(data['senha_atual']):
            raise serializers.ValidationError({"senha_atual": "Senha atual incorreta."}) # raise para a execução e lança o erro

        # Verifica se a nova senha e a confirmação coincidem
        if data['nova_senha'] != data['nova_senha_confirm']:
            raise serializers.ValidationError({"nova_senha_confirm": "As novas senhas não coincidem."}) 

        return data


    
class SolicitarRedefinicaoSenhaSerializer(serializers.Serializer):
    """
    Recebe o e-mail do usuário, gera o token nativo do Django e envia o link.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Não existe usuário com este e-mail.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Gera o identificador do usuário e o token de segurança do Django
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        link_reset = f"https://nathanmuniz18.github.io/checkpoint-web/#/redefinir-senha?uid={uid}&token={token}"
        
        send_mail(
            subject="Redefinição de Senha - Checkpoint",
            message=f"Olá {user.username},\n\nAcesse o link abaixo para redefinir sua senha:\n{link_reset}\n\nSe você não solicitou isso, ignore este e-mail.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

class RedefinirSenhaEmailSerializer(serializers.Serializer):
    """
    Recebe o uid e token do e-mail junto com a nova senha para validar e salvar.
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    nova_senha = serializers.CharField(write_only=True)
    nova_senha_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['nova_senha'] != data['nova_senha_confirm']:
            raise serializers.ValidationError({"nova_senha_confirm": "As senhas não coincidem."})
        
        try:
            # Decodifica o ID do usuário e busca no banco
            uid_decoded = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Link de redefinição inválido ou corrompido."})
        
        # Valida se o token pertence a este usuário e se ainda está no prazo
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({"token": "Token inválido ou expirado."})
        
        # Guarda o usuário no contexto para o método save usar
        self.context['user'] = user
        return data

    def save(self):
        user = self.context['user']
        user.set_password(self.validated_data['nova_senha'])
        user.save()
