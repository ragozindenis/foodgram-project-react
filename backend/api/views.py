import io
import os

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import RecipeFilter
from api.pagination import CustomPaginator
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnlyPermission
from api.serializers import (ChangePasswordSerializer, FavoriteSerializer,
                            IngredientSerializer, RecipeCreateSerializer,
                            RecipeReadSerializer, ShopingCartSerializer,
                            TagSerializer, UsersSerializer,
                            UsersSubscribeSerializer,
                            UserSubscriptionsSerializer)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscribe, User


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = CustomPaginator

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions
        that this view requires.
        """
        if self.action == "list":
            permission_classes = [
                IsAdminOrReadOnly,
            ]
        elif self.action == "create":
            permission_classes = [
                AllowAny,
            ]
        elif self.action == "retrieve":
            permission_classes = [
                IsAdminOrReadOnly,
            ]
        else:
            permission_classes = [
                IsAuthenticated,
                IsAuthorOrReadOnlyPermission,
            ]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=(IsAuthenticated,),
        serializer_class=UsersSerializer,
    )
    def me(self, request):
        user = self.request.user
        if request.method == "GET":
            serializer = UsersSerializer(user)
            return Response(serializer.data)
        return Response("method wrong", status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["post"],
        url_path="set_password",
        permission_classes=(IsAuthenticated,),
        serializer_class=ChangePasswordSerializer,
    )
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response("new password set", status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs["pk"])
        if request.method == "POST":
            if Subscribe.objects.filter(
                user=request.user, author=author
            ).exists():
                return Response(
                    "Вы уже подписаны на данного пользователя",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if request.user == author:
                return Response(
                    "Нельзя подписаться на самого себя",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UsersSubscribeSerializer(
                author, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=request.user, author=author)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"Success": "Успешная подписка"},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        if request.method == "DELETE":
            get_object_or_404(
                Subscribe, user=request.user, author=author
            ).delete()
            return Response(
                {"detail": "Успешная отписка"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"detail": "-__-"},
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        pagination_class=CustomPaginator,
        permission_classes=(IsAuthenticated,),
        serializer_class=UsersSerializer,
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserSubscriptionsSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ("^name",)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnlyPermission,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs["pk"])

        if request.method == "POST":
            if Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    "Вы уже добавили этот рецепт",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = FavoriteSerializer(
                recipe, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Favorite.objects.create(user=request.user, recipe=recipe)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"Success": "Успешное добавление рецепта в избранное"},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        if request.method == "DELETE":
            if not Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    "Вы уже удалили этот рецепт",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            get_object_or_404(
                Favorite, user=request.user, recipe=recipe
            ).delete()
            return Response(
                {"detail": "Успешное удаление рецепта из избранного"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"detail": "-__-"},
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs["pk"])

        if request.method == "POST":
            if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    "Вы уже добавили этот рецепт",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = ShopingCartSerializer(
                recipe, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"Success": "Успешное добавление рецепта в список покупок"},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        if request.method == "DELETE":
            if not ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    "Вы уже удалили этот рецепт",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            get_object_or_404(
                ShoppingCart, user=request.user, recipe=recipe
            ).delete()
            return Response(
                {"detail": "Успешное удаление рецепта из списка покупок"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"detail": "-__-"},
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (
            ShoppingCart.objects.filter(user=request.user.id)
            .values_list(
                "recipe__ingredients__name",
                "recipe__ingredients__measurement_unit",
            )
            .distinct()
            .annotate(total=Sum("recipe__ingredients_recipe__amount"))
        )
        buffer = io.BytesIO()
        path = "data"
        font = TTFont(
            "Arial",
            os.path.join(path, "Arial.ttf"),
        )
        pdfmetrics.registerFont(font)
        s = Canvas(buffer)
        s.setFont("Arial", 35)
        s.setPageSize((650, 500))
        start_y = 400
        start_x = 10
        s.drawString(10, 450, "Ваш список ингредиентов:")
        s.setFont("Arial", 20)
        page = 1
        for ing in ingredients:
            start_y -= 50
            s.drawString(
                start_x,
                start_y,
                "{}, мера - {}, количество - {}.".format(*ing),
            )
            if start_y == 50:
                page += 1
                s.showPage()
                s.setFont("Arial", 35)
                s.drawString(10, 450, f"Страница - {page}")
                s.setFont("Arial", 20)
                start_y = 400
        s.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename="Shopping_list.pdf"
        )
