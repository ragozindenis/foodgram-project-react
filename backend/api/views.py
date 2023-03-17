import csv

from django.db.models import Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.models import Subscribe, User

from .filters import RecipeFilter
from .pagination import CustomPaginator
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnlyPermission
from .serializers import (ChangePasswordSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, ShopingCartSerializer,
                          TagSerializer, UsersSerializer,
                          UsersSubscribeSerializer,
                          UserSubscriptionsSerializer)


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
                IsAuthenticated,
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
                {"detail": "succes deleted recipe from favorite"},
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
                {"detail": "succes deleted recipe from shopping list"},
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
        fields = ["Name", "Measurement_unit", "Amount"]
        with open("Your_ingredients.csv", "w") as file:
            response = HttpResponse(content_type="text/csv")
            response[
                "Content-Disposition"
            ] = 'attachment; filename="export.csv"'
            write = csv.writer(response, file)
            write.writerow(fields)
            write.writerows(ingredients)

            return response
