from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet, TagViewSet, RecipeViewSet, IngredientViewSet
)

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='users')
# router.register('tokens', TokenViewSet, basename='tokens')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # path('s/<str:short_hash>/', RecipeViewSet.as_view({'get': 'redirect_short_link'}), name='recipe-short-link')

]