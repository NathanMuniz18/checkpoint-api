from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT (SimpleJWT)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),# Rota para fazer login e obter os tokens (Access e Refresh)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Rota para usar o token Refresh e renovar o token Access expirado
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'), # Rota opcional para verificar se um token ainda é válido

    # Swagger
    # Gera o esquema OpenAPI base da nossa API em formato JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Renderiza a interface interativa do Swagger UI usando o esquema acima
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui'),

    # Interface alternativa de documentação (ReDoc)
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='schema-redoc'),

    # ROTAS DOS NOSSOS APPS
    path('api/usuarios/', include('usuarios.urls')),
    path('api/jogos/', include('jogos.urls')),
]