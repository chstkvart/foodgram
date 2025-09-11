from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views import RecipeViewSet
schema_view = get_schema_view(
   openapi.Info(
      title="Foodgram API",  # Измените название
      default_version='v1',
      description="Документация для приложения Foodgram",
      contact=openapi.Contact(email="admin@foodgram.ru"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    
    # Документация Swagger/ReDoc
    path(
       'swagger<format>/',
       schema_view.without_ui(cache_timeout=0),
       name='schema-json'
    ),
    path(
       'swagger/',
       schema_view.with_ui('swagger', cache_timeout=0),
       name='schema-swagger-ui'
    ),
    path(
       'redoc/',
       schema_view.with_ui('redoc', cache_timeout=0),
       name='schema-redoc'
    ),
    # Добавьте также путь для api/docs
    path(
       'api/docs/',
       schema_view.with_ui('redoc', cache_timeout=0),
       name='schema-redoc-api'
    ),
    path('s/<str:short_hash>/', RecipeViewSet.as_view({'get': 'redirect_short_link'}), name='recipe-short-link')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)