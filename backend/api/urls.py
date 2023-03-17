from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from .custom_routers import PutMthodNotAllow
from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router_no_put = PutMthodNotAllow()
router_v1 = routers.DefaultRouter()
router_v1.register("users", UserViewSet, basename="user")
router_no_put.register("recipes", RecipeViewSet, basename="recipe")
router_v1.register("tags", TagViewSet, basename="tag")
router_v1.register("ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    path("", include(router_v1.urls)),
    path("", include(router_no_put.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
