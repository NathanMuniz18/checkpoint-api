from rest_framework import serializers
from .models import Jogo, JogoUsuario

class JogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jogo
        fields = ['id', 'rawg_id', 'nome', 'capa_url', 'plataforma', 'slug']


class JogoUsuarioSerializer(serializers.ModelSerializer):
    # Aninhamos o serializer do jogo para leitura. 
    # Assim, o frontend recebe não apenas o ID do jogo, mas também a capa e o nome para desenhar na tela.
    jogo_detalhes = JogoSerializer(source='jogo', read_only=True)

    class Meta:
        model = JogoUsuario
        fields = [
            'id', 
            'jogo', 
            'jogo_detalhes', 
            'status', 
            'horas_jogadas', 
            'adicionado_em', 
            'atualizado_em'
        ]
        # O usuário não precisa ser enviado no JSON, o backend pega ele automaticamente pelo Token JWT
        read_only_fields = ['adicionado_em', 'atualizado_em']

    def validate(self, data):
        # Pegamos o usuário que está fazendo a requisição pelo token
        usuario = self.context['request'].user
        jogo = data.get('jogo')

        # Se for uma criação (não tem instância ainda), checamos a regra UniqueConstraint
        if not self.instance and JogoUsuario.objects.filter(usuario=usuario, jogo=jogo).exists():
            raise serializers.ValidationError({"jogo": "Este jogo já está cadastrado na sua jornada."})

        return data

    def create(self, validated_data):
        # Injeta o usuário logado automaticamente antes de salvar no banco
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)