from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import viewsets, filters, mixins
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.decorators import action

from food.models import Recipe, Tag, Ingredients, Favorite,\
     ShoppingCart, IngredientToRecipe
from user.models import Follow
from .serializers import (
    IngredientsSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    FavoriteSerializer,
    FollowSerializer,
    CustomUserSerializer
    )
from .filters import MyFilterSet, IngredientFilter
from .pagination import CustomPagination
from .premissions import AuthorOrAdmin

User = get_user_model()


class CustomUserViewSet(UserViewSet):

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination
    serializer_class = CustomUserSerializer

    def get_queryset(self):
        return User.objects.all()


class FollowListMixin(mixins.ListModelMixin, viewsets.GenericViewSet):

    serializer_class = FollowSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class FollowMixin(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = FollowSerializer
    queryset = User.objects.all()

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        author = get_object_or_404(User, pk=user_id)

        instance = Follow.objects.filter(
            user=request.user, author=author)

        if not instance:
            raise serializers.ValidationError(
                'Вы не подписаны на этого пользователя'
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeWiewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    filter_class = MyFilterSet
    pagination_class = CustomPagination
    permission_classes = AuthorOrAdmin,
    ordering = ['-pub_date']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @staticmethod
    def send_message(ingredients):

        shopping_list = 'Купить в магазине:'
        for ingredient in ingredients:
            shopping_list += (
                f"\n{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['amount']}")
        file = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        return response

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):

        ingredients = IngredientToRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        return self.send_message(ingredients)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientMixin(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_backends = (IngredientFilter, )
    search_fields = ('^name', )


class FavoriteMixin(
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):

    queryset = Recipe.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        instance = Favorite.objects.filter(
            user=request.user, recipe=recipe)

        if not instance:
            raise serializers.ValidationError(
                'В корзине нет данного товара'
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartMixin(
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):

    permission_classes = IsAuthenticated
    queryset = Recipe.objects.all()
    serializer_class = ShoppingCartSerializer

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        instance = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe)
        if not instance:
            raise serializers.ValidationError(
                'В корзине нет данного товара'
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)