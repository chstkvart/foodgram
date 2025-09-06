from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet, TagViewSet, RecipeViewSet, IngredientViewSet
)

router = routers.DefaultRouter()
# router.register('custom-users', UserViewSet, basename='custom-users')
# router.register('tokens', TokenViewSet, basename='tokens')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

]