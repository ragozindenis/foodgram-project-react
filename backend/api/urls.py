from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from api.custom_routers import PutMethodNotAllow
from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router_no_put_v1 = PutMethodNotAllow()
router_no_put_v1.register("users", UserViewSet, basename="user")
router_no_put_v1.register("recipes", RecipeViewSet, basename="recipe")
router_no_put_v1.register("tags", TagViewSet, basename="tag")
router_no_put_v1.register(
    "ingredients", IngredientViewSet, basename="ingredient"
)

urlpatterns = [
    path("", include(router_no_put_v1.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
