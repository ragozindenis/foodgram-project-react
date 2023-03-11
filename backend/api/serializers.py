import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class UsersSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)

        try:
            user.set_password(validated_data["password"])
            user.save()
        except KeyError:
            pass

        return user

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Subscribe.objects.filter(author=obj, user=user).exists()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
        )
        extra_kwargs = {"password": {"write_only": True}}


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("new_password", "current_password")

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError(
                "Current password does not match"
            )
        return value

    def validate(self, data):
        if data["current_password"] == data["new_password"]:
            raise serializers.ValidationError(
                {"message": ["the password must not match the old one"]}
            )
        return data


class UsersSubscribeSerializer(serializers.Serializer):
    class Meta:
        model = Subscribe
        fields = ("user", "author")


class RecipeAuthorShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSubscriptionsSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Subscribe.objects.filter(author=obj, user=user).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = RecipeAuthorShortSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(
        write_only=True, validators=[MinValueValidator(1)]
    )

    class Meta:
        model = IngredientRecipe
        fields = ("id", "amount")


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UsersSerializer(
        default=serializers.CurrentUserDefault(), read_only=True
    )
    ingredients = IngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate_ingredients(self, value):
        ingredients_list = []
        for ingredient in value:
            if ingredient["id"] in ingredients_list:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяеться"
                )
            ingredients_list.append(ingredient["id"])
            return value

    def validate_tags(self, value):
        tags_list = []
        for tag in value:
            if tag in tags_list:
                raise serializers.ValidationError(
                    "Теги не должны повторяеться"
                )
            tags_list.append(tag)
            return value

    def add_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                ingredient_id=ingredient.get("id"),
                amount=ingredient.get("amount"),
                recipe=recipe,
            )

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(recipe, ingredients)
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        super().update(instance, validated_data)
        instance.ingredients.clear()
        instance.tags.set(tags)
        self.add_ingredients(instance, ingredients)
        instance.save()
        return

    def get_is_favorited(self, obj):
        return (
            self.context.get("request").user.is_authenticated
            and Favorite.objects.filter(
                user=self.context["request"].user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get("request").user.is_authenticated
            and ShoppingCart.objects.filter(
                user=self.context["request"].user, recipe=obj
            ).exists()
        )


class RecipeReadSerializer(RecipeCreateSerializer):
    author = UsersSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            "ingredient_recipe__amount",
        )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class FavoriteSerializer(serializers.Serializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")

    def validate(self, data):
        return data


class ShopingCartSerializer(serializers.Serializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")

    def validate(self, data):
        return data


class GetShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ["recipe"]
