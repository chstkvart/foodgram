import shortuuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


MAX_COOKING_TIME = 32_000
MIN_COOKING_TIME = 1
MAX_AMOUNT = 32_000
MIN_AMOUNT = 1


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=50
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Уникальный слаг',
        max_length=200
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Изображени',
        upload_to='recipes/'
    )
    text = models.TextField(
        verbose_name='Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ]
    )
    short_hash = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткий хеш для ссылки'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_hash:
            self.short_hash = self.generate_short_hash()
        super().save(*args, **kwargs)

    def generate_short_hash(self):
        return shortuuid.ShortUUID().random(length=7)


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ['recipe__name']

    def __str__(self):
        return self.recipe.name


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Пользовательские корзины'
        ordering = ['-id']

    def __str__(self):
        return self.user.username
