from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField("Название ингредиента", max_length=200)
    measurement_unit = models.CharField("Единица измерения", max_length=200)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("id",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    name = models.CharField("Название тега", max_length=200, unique=True)
    color = ColorField(
        "Цвет",
        max_length=7,
        unique=True,
    )
    slug = models.SlugField("Слаг", max_length=200, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

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
    image = models.ImageField("Картинка", upload_to="")
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
        validators=[
            MinValueValidator(
                1, message="Убедитесь, что это значение больше либо равно 1."
            ),
            MaxValueValidator(
                1000,
                message="Убедитесь, что это значение меньше либо равно 1000.",
            ),
        ],
        verbose_name="Время приготовления",
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredients_recipe",
        verbose_name="Название ингредиента",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients_recipe",
        verbose_name="Название рецепта",
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"

    def __str__(self):
        return f"{self.ingredient}{self.recipe}{self.amount}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_user",
        verbose_name="Избранное пользователя",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite_recipe",
        verbose_name="Избранный рецепт",
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
        verbose_name="Список покупок пользователя",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_recipe",
        verbose_name="Рецепт в списке покупок",
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
