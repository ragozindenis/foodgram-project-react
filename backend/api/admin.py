from django.contrib import admin
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscribe, User


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through


@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ["pk", "email", "username", "first_name", "last_name"]
    search_fields = ["pk", "email", "username", "first_name", "last_name"]
    list_filter = ["email", "username"]


@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "color", "slug"]
    search_fields = ["pk", "name", "color", "slug"]


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ["pk", "author", "name", "text", "cooking_time"]
    search_fields = ["pk", "author", "name", "tags"]
    inlines = [
        IngredientInline,
    ]
    exclude = ("ingredients",)


@admin.register(Ingredient)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "measurement_unit"]
    search_fields = ["pk", "name", "measurement_unit"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "recipe"]
    search_fields = ["pk", "user", "recipe"]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "recipe"]
    search_fields = ["pk", "user", "recipe"]


@admin.register(Subscribe)
class SubscribesAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "author", "created"]
    search_fields = ["pk", "user", "author", "created"]
