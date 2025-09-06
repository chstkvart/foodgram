import base64
from rest_framework import serializers
from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart, RecipeIngredients
from users.models import User, Follow
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate
from djoser.serializers import UserCreateSerializer, UserSerializer, TokenCreateSerializer
from rest_framework.authtoken.models import Token

class Base64ImageField(serializers.ImageField):
    """Сериализатор для картинок."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name='temp.' + ext
            )
        return super().to_internal_value(data)


class UsersSerializer(serializers.ModelSerializer):
    """Список пользователей."""

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class UserCreateSerializer(UserCreateSerializer):
    """Регистрация пользователя."""

    email = serializers.EmailField(
        max_length=254,
        required=True
    )
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=150,
        error_messages={
            'invalid': 'Имя пользователя содержит недопустимые символы.'
        }
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True
    )
    password = serializers.CharField(
        required=True
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def validate(self, data):
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError(
                {'username': 'Имя пользователя уже занято.'}
            )
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {'email': 'Электронная почта уже используется.'}
            )
        return data


class UserSerializer(UserSerializer):
    """Профиль пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user,
            author=obj
        ).exists()

    def update(self, instance, validated_data):
        if 'avatar' in validated_data:
            instance.avatar = validated_data.get('avatar')
            instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный пароль')
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        if user.check_password(value):
            raise serializers.ValidationError(
                'Новый пароль не должен совпадать с текущим'
            )
        return value

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class TokenSerializer(TokenCreateSerializer):
    """Получение токена авторизации."""

    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            email=data.get("email"),
            password=data.get("password")
        )
        if not user:
            raise serializers.ValidationError("Неверный email или пароль")
        data["user"] = user
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэга."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Получение ингредиента."""
    
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientListSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""
    
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    measurement_unit = serializers.CharField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False
    
    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField()
    tags = serializers.ListField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    # def validate_ingredients(self, value):
    #     if not value:
    #         raise serializers.ValidationError(
    #             'Список ингредиентов не может быть пустым'
    #         )
    #     ingredient_ids = set()
    #     for ingredient_data in value:
    #         ingredient_id = ingredient_data.get('id')
    #         amount = ingredient_data.get('amount')
    #         if not ingredient_id or not amount:
    #             raise serializers.ValidationError(
    #                 "Каждый ингредиент должен содержать id и amount"
    #             )
    #         if amount < 1:
    #             raise serializers.ValidationError(
    #                 "Количество ингредиента должно быть не менее 1."
    #             )
    #         if ingredient_id in ingredient_ids:
    #             raise serializers.ValidationError(
    #                 "Ингредиенты не должны повторяться."
    #             )
    #         ingredient_ids.add(ingredient_id)
    #         try:
    #             Ingredient.objects.get(id=ingredient_id)
    #         except Ingredient.DoesNotExist:
    #             raise serializers.ValidationError(
    #                 f"Ингредиент с id {ingredient_id} не существует."
    #             )
    #     return value

    # def validate_tags(self, value):
    #     if not value:
    #         raise serializers.ValidationError(
    #             "Список тегов не может быть пустым."
    #         )
    #     existing_tags = Tag.objects.filter(id__in=value)
    #     if len(existing_tags) != len(value):
    #         raise serializers.ValidationError("Один или несколько тегов не существуют.")
    #     return value

    # def validate_cooking_time(self, value):
    #     if value < 1:
    #         raise serializers.ValidationError(
    #             "Время приготовления должно быть не менее 1 минуты."
    #         )
    #     return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(
                RecipeIngredients(
                    recipe=recipe,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount']
                )
            )
        RecipeIngredients.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = []
            for ingredient_data in ingredients_data:
                recipe_ingredients.append(
                    RecipeIngredients(
                        recipe=instance,
                        ingredient_id=ingredient_data['id'],
                        amount=ingredient_data['amount']
                    )
                )
            RecipeIngredients.objects.bulk_create(recipe_ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeShortLinkSerializer(serializers.Serializer):
    short_link = serializers.SerializerMethodField()

    def get_short_link(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/s/{obj.id}/')
        return f'/s/{obj.id}/'


class ShoppingCartDownloadSerializer(serializers.Serializer):

    def get_shopping_list_data(self, user):
        shopping_cart = ShoppingCart.objects.filter(user=user).select_related('recipe')
        ingredients_dict = {}
        for item in shopping_cart:
            recipe_ingredients = RecipeIngredients.objects.filter(
                recipe=item.recipe
            ).select_related('ingredient')
            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient
                key = (ingredient.id, ingredient.name, ingredient.measurement_unit)
                if key in ingredients_dict:
                    ingredients_dict[key] += recipe_ingredient.amount
                else:
                    ingredients_dict[key] = recipe_ingredient.amount
        shopping_list = []
        for (ingredient_id, name, measurement_unit), amount in ingredients_dict.items():
            shopping_list.append({
                'id': ingredient_id,
                'name': name,
                'measurement_unit': measurement_unit,
                'amount': amount
            })
        return shopping_list

    def generate_text_content(self, shopping_list):
        content = "Список покупок:\n\n"
        content += "=" * 50 + "\n"
        for item in shopping_list:
            content += f"• {item['name']} - {item['amount']} {item['measurement_unit']}\n"
        content += "=" * 50 + "\n"
        content += f"Всего позиций: {len(shopping_list)}\n"
        return content

    def generate_csv_content(self, shopping_list):
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Название', 'Количество', 'Единица измерения'])
        for item in shopping_list:
            writer.writerow([item['name'], item['amount'], item['measurement_unit']])
        return output.getvalue()

    def generate_pdf_content(self, shopping_list):
        return self.generate_text_content(shopping_list)
 

class ShoppingCartAddSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.recipe.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.recipe.image.url)
            return obj.recipe.image.url
        return None

    def validate(self, data):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('id')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise serializers.ValidationError("Рецепт не найден.")
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в списке покупок.")
        data['recipe'] = recipe
        data['user'] = user
        return data

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)


class ShoppingCartRemoveSerializer(serializers.Serializer):

    def validate(self, data):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('id')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise serializers.ValidationError("Рецепт не найден.")
        if not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепта нет в списке покупок.")
        data['recipe'] = recipe
        data['user'] = user
        return data

    def delete(self):
        user = self.validated_data['user']
        recipe = self.validated_data['recipe']
        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Вы не авторизованы")
        user = request.user
        recipe = validated_data.get('recipe')
        favorite, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError("Рецепт уже добавлен в избранное")
        return favorite


class FavoriteDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'recipe']

    def destroy(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Вы не авторизованы")
        user = request.user
        recipe = validated_data.get('recipe')
        try:
            favorite = Favorite.objects.get(user=user, recipe=recipe)
            favorite.delete()
            return {'detail': 'Рецепт удален из избранного'}
        except Favorite.DoesNotExist:
            raise serializers.ValidationError("Рецепт не найден в избранных")
        

class FollowSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit') if request else None
        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except (ValueError, TypeError):
                pass
        return RecipeShortLinkSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()
    
    def validate(self, data):
        """Валидация данных подписки (используется только при создании)"""
        if self.context.get('request') and self.context['request'].method == 'POST':
            user = self.context['request'].user
            author_id = self.context['view'].kwargs.get('id')
            if user == author:
                raise serializers.ValidationError("Нельзя подписаться на себя.")
            if Follow.objects.filter(user=user, author=author).exists():
                raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
            data['author'] = author
            data['user'] = user
        return data

    # def create(self, validated_data):
    #     """Создание подписки (только для POST запросов)"""
    #     try:
    #         follow = Follow.objects.create(
    #             user=validated_data['user'],
    #             author=validated_data['author']
    #         )
    #         return follow