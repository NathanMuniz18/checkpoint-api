from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Persona

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    # Definimos os campos de senha para que o frontend possa enviar
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, data):
        # 1. Confere se as senhas são iguais
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "As senhas informadas não coincidem."})
        
        # 2. Confere se o email já está em uso no banco
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "Este endereço de e-mail já está cadastrado."})
            
        return data

    def create(self, validated_data):
        # Remove a confirmação de senha (pois não se salva isso no banco)
        validated_data.pop('password_confirm')
        
        # Cria o usuário criptografando a senha de forma segura
        usuario = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        
        # Cria automaticamente o perfil "Persona" em branco para esse usuário
        Persona.objects.create(usuario=usuario)
        
        return usuario