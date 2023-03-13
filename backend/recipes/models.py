from colorfield.fields import ColorField
from django.core import validators
from django.core.validators import MinValueValidator
from django.db import models
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Ингредиент"
        ordering = ("id",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    name = models.CharField("Название тега", max_length=200, unique=True)
    color = ColorField(
        "Цвет",
        max_length=7,
        unique=True,
        validators=[
            validators.RegexValidator(
                regex=r"^#[a-fA-F0-9]{6}$",
                message="Неверное значение HEX-кода",
            )
        ],
    )
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Тэг"

    def __str__(self):
        return f"{self.name}, {self.color}, {self.slug}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    name = models.CharField("Название рецепта", max_length=200)
    image = models.ImageField(
        upload_to="",
    )
    text = models.TextField("Описание рецепта")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientRecipe",
        related_name="ingredients",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag, related_name="tags", verbose_name="Тэги"
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1, message="Ошибка валидации")],
        verbose_name="Cooking time",
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = "Рецепт"

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipe",
        verbose_name="Название ингредиента",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients_recipe",
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Amount"
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"

    def __str__(self):
        return f"{self.ingredient}{self.recipe}{self.amount}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_user",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite_recipe",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_user",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_recipe",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
