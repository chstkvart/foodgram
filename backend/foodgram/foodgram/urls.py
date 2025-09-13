from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('s/<str:short_hash>/', RecipeViewSet.as_view(
        {'get': 'redirect_short_link'}), name='recipe-short-link')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
