from django.conf import settings
from django.db import models

class Persona(models.Model):
    # Liga este perfil a um usuário oficial do Django
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil"
    )
    bio = models.TextField(max_length=500, blank=True, default="")
    foto = models.URLField(blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
