from django.contrib import admin
from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class UsersAdmin(admin.ModelAdmin):
    list_display = ["pk", "email", "username", "first_name", "last_name"]
    search_fields = ["pk", "email", "username", "first_name", "last_name"]
    list_filter = ["email", "username"]


class TagsAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "color", "slug"]
    search_fields = ["pk", "name", "color", "slug"]


class RecipesAdmin(admin.ModelAdmin):
    list_display = ["pk", "author", "name", "text", "cooking_time"]
    search_fields = ["pk", "author", "name", "tags"]


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "measurement_unit"]
    search_fields = ["pk", "name", "measurement_unit"]


admin.site.register(Recipe, RecipesAdmin)
admin.site.register(User, UsersAdmin)
admin.site.register(Tag, TagsAdmin)
admin.site.register(Ingredient, IngredientsAdmin)
