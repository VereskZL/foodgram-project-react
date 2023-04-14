from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet, FavoriteMixin, FollowListMixin,
                    FollowMixin, IngredientMixin, RecipeWiewSet,
                    ShoppingCartMixin, TagViewSet)

router_v1 = routers.DefaultRouter()
router_v1.register('tags', TagViewSet)
router_v1.register('recipes', RecipeWiewSet, basename='recipes')
router_v1.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartMixin,
    basename='shopping_cart')
router_v1.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavoriteMixin,
    basename='favorite')
router_v1.register(
    'ingredients',
    IngredientMixin,
    basename='ingredients')
router_v1.register(r'users/(?P<user_id>\d+)/subscribe',
                   FollowMixin,
                   basename='subscribe')
router_v1.register('users/subscriptions',
                   FollowListMixin,
                   basename='subscriptions')
router_v1.register('users', CustomUserViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
