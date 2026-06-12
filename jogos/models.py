from django.conf import settings
from django.db import models

class Jogo(models.Model):
    rawg_id = models.PositiveIntegerField(unique=True, db_index=True)
    nome = models.CharField(max_length=180)
    capa_url = models.URLField(blank=True, default="")
    plataforma = models.CharField(max_length=220, blank=True, default="")
    slug = models.SlugField(max_length=220, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

class JogoUsuario(models.Model):
    class Status(models.TextChoices):
        VOU_JOGAR = "vou_jogar", "Vou Jogar"
        TO_JOGANDO = "to_jogando", "Tô jogando"
        JA_ZEREI = "ja_zerei", "Já Zerei"
        DESISTI = "desisti", "Desisti"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jogos_usuario",
    )
    jogo = models.ForeignKey(
        Jogo,
        on_delete=models.CASCADE,
        related_name="usuarios",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.VOU_JOGAR,
    )
    horas_jogadas = models.PositiveIntegerField(default=0)
    adicionado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "jogo"],
                name="jogo_unico_por_usuario",
            )
        ]
        ordering = ["-atualizado_em"]

    def __str__(self):
        return f"{self.usuario} - {self.jogo.nome}"