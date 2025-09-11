from django.contrib import admin
from .models import (
    Ingredient, Tag, Recipe, RecipeIngredients,
    Favorite, ShoppingCart)
from users.models import User, Follow

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    list_editable = ('slug',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorites_count')
    list_display_links = ('name',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    readonly_fields = ('get_favorites_count_display',)
    fields = ['name', 'author', 'get_favorites_count_display', 'image', 'text', 'ingredients', 'tags', 'cooking_time']
    filter_horizontal = ['tags']
    

    def get_favorites_count(self, obj):
        return obj.favorites.count()
    get_favorites_count.short_description = 'В избранном'

    def get_favorites_count_display(self, obj):
        return obj.favorites.count()
    get_favorites_count_display.short_description = 'Количество добавлений в избранное'

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Теги'


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('recipe',)
    search_fields = ('recipe__name', 'ingredient__name')
    list_editable = ('amount',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff')
    list_display_links = ('username',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_editable = ('is_staff',)
    list_filter = ('is_staff', 'is_superuser')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_display_links = ('user',)
    search_fields = ('user__username', 'author__username')