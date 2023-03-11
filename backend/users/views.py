from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Subscribe, User
from .pagination import CustomPaginator
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnlyPermission
from .serializers import (ChangePasswordSerializer, UsersSerializer,
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
            else:
                serializer = UsersSubscribeSerializer(
                    author, data=request.data, context={"request": request}
                )
                serializer.is_valid(raise_exception=True)
                Subscribe.objects.create(user=request.user, author=author)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

        if request.method == "DELETE":
            get_object_or_404(
                Subscribe, user=request.user, author=author
            ).delete()
            return Response(
                {"detail": "Успешная отписка"},
                status=status.HTTP_204_NO_CONTENT,
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
