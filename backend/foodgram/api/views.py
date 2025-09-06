from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
# from rest_framework.views import APIView
from users.models import Follow, User
from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart
from .serializers import (
    UsersSerializer, UserCreateSerializer, UserSerializer, PasswordChangeSerializer,
     TagSerializer, IngredientSerializer, RecipeSerializer,
    RecipeCreateUpdateSerializer, RecipeShortLinkSerializer, ShoppingCartDownloadSerializer,
    ShoppingCartAddSerializer, ShoppingCartRemoveSerializer, FavoriteSerializer,
    FavoriteDeleteSerializer, FollowSerializer, Base64ImageField
)
from django.shortcuts import get_object_or_404
from .permissions import ReadOnly, IsAuthorOrReadOnly, IsAdmin, IsOwnerOrReadOnly
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import logout
# from rest_framework.authtoken.models import Token
# from rest_framework.parsers import MultiPartParser, JSONParser
# from django_filters.rest_framework import DjangoFilterBackend
from .paginaion import CustomPageNumberPagination
from djoser.views import TokenCreateView
from django.http import HttpResponse

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'me']:
            return UserSerializer
        return UsersSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['list', 'retrieve']:
            return [ReadOnly()]
        elif self.action in ['me']:
            return [permissions.IsAuthenticated()]
        return [ReadOnly()]

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == "PATCH":
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True
            )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {"detail": "Поле 'avatar' обязательно."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserSerializer(
                user,
                data={'avatar': request.data['avatar']}, 
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            if not user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='set_password'
    )
    def set_password(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(
            data=request.data,
            contex={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(follow__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        if pages is not None:
            serializer = FollowSerializer(pages, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        return Response(
            {"detail": "Вы ни на кого не подписаны."},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {"detail": "Нельзя подписаться на себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, author=author)
            recipes_limit = request.query_params.get('recipes_limit')
            serializer = FollowSerializer(
                author,
                context={
                    'request': request,
                    'recipes_limit': recipes_limit
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, author=author).first()
            if not follow:
                return Response(
                    {"detail": "Вы не подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

# class TokenViewSet(TokenCreateView):
#     serializer_class = TokenSerializer
#     permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action == ['retrieve', 'list']:
            return RecipeSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        else:
            return [permissions.AllowAny()]

    @action(
        detail=True,
        methods=['get'],
        serializer_class=RecipeShortLinkSerializer
    )
    def get_link(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):        
        serializer = ShoppingCartDownloadSerializer(context={'request': request})
        shopping_list = serializer.get_shopping_list_data(request.user)
        content = serializer.generate_text_content(shopping_list)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def add_delete_shopping_cart(self, request):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = ShoppingCartAddSerializer(data={'recipe': recipe.id}, context={'request': request, 'view': self})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"detail": "Рецепт добавлен в корзину."}, status=status.HTTP_201_CREATED) 
        elif request.method == 'DELETE':
            serializer = ShoppingCartRemoveSerializer(data={'recipe': recipe.id}, context={'request': request, 'view': self})
            serializer.is_valid(raise_exception=True)
            serializer.delete()
            return Response({"detail": "Рецепт удален из корзины."}, status=status.HTTP_204_NO_CONTENT)
        
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже добавлен в избранное."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
            if not favorite:
                return Response(
                    {"detail": "Рецепт не найден в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset