from rest_framework import serializers
from .models import Jogo, JogoUsuario


class JogoSerializer(serializers.ModelSerializer):
    """
    Serializer para o model Jogo.

    Usado para serializar os resultados da busca na RAWG
    e para exibir detalhes do jogo dentro de JogoUsuarioSerializer.
    """
    class Meta:
        model = Jogo
        fields = ['id', 'rawg_id', 'nome', 'capa_url', 'plataforma', 'slug']


class JogoUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o model JogoUsuario.

    Aninha o JogoSerializer para que o frontend receba
    os detalhes do jogo (nome, capa) junto com o status e horas jogadas.
    """
    # Aninhamos o serializer do jogo para leitura
    # Assim o frontend recebe nome e capa sem precisar fazer outra requisição
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
        # O usuário é injetado automaticamente pelo backend via token JWT
        read_only_fields = ['adicionado_em', 'atualizado_em']

    def validate(self, data):
        """
        Valida que o jogo não está duplicado na jornada do usuário.

        :param dict data: dados enviados pelo frontend
        :return: dados validados
        :raises ValidationError: se o jogo já estiver na jornada
        """
        usuario = self.context['request'].user
        jogo = data.get('jogo')

        # Se for criação, verifica a constraint de jogo único por usuário
        if not self.instance and JogoUsuario.objects.filter(usuario=usuario, jogo=jogo).exists():
            raise serializers.ValidationError({"jogo": "Este jogo já está cadastrado na sua jornada."})

        return data

    def create(self, validated_data):
        """
        Cria a relação JogoUsuario injetando o usuário logado automaticamente.

        :param dict validated_data: dados já validados
        :return: relação JogoUsuario criada
        :rtype: JogoUsuario
        """
        # Injeta o usuário logado antes de salvar no banco
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)