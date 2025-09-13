from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Follow, User

from .filters import RecipeFilter
from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly, ReadOnly
from .serializers import (
    FollowSerializer,
    IngredientSerializer,
    PasswordChangeSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    RecipeShortLinkSerializer,
    ShoppingCartAddSerializer,
    ShoppingCartDownloadSerializer,
    ShoppingCartRemoveSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
    UsersSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'me', 'avatar', 'set_password']:
            return UserSerializer
        return UsersSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['list', 'retrieve']:
            return [ReadOnly()]
        elif self.action in ['me', 'avatar', 'set_password']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['subscribe', 'subscriptions']:
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
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"avatar": request.build_absolute_uri(
                    user.avatar.url) if user.avatar else None},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            if user.avatar:
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
            context={'request': request}
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
        subscriptions = Follow.objects.filter(
            user=request.user).select_related('author').order_by('id')
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {"detail": 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(
                follow,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, author=author).first()
            if not follow:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return RecipeSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        elif self.action == 'get_link':
            return RecipeShortLinkSerializer
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
        serializer_class=RecipeShortLinkSerializer,
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, context={'request': request})
        short_link = serializer.data['short_link']
        return Response({'short-link': short_link})

    @action(
        detail=False,
        methods=['get'],
        url_path='s/(?P<short_hash>[^/.]+)'
    )
    def redirect_short_link(self, request, short_hash=None):
        recipe = get_object_or_404(Recipe, short_hash=short_hash)
        return redirect(f'/recipes/{recipe.id}/')

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        serializer = ShoppingCartDownloadSerializer(
            context={'request': request})
        shopping_list = serializer.get_shopping_list_data(request.user)
        content = serializer.generate_text_content(shopping_list)
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='shopping_cart'
    )
    def add_delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = ShoppingCartAddSerializer(
                data={}, context={'request': request, 'recipe': recipe})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'detail': 'Рецепт добавлен в корзину'},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            serializer = ShoppingCartRemoveSerializer(
                data={}, context={'request': request, 'recipe': recipe})
            serializer.is_valid(raise_exception=True)
            serializer.delete()
            return Response(
                {'detail': 'Рецепт удален из корзины'},
                status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(
                user=user, recipe=recipe).first()
            if not favorite:
                return Response(
                    {'detail': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset
