from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from users.models import Follow, User
from .filters import MyFilterSet
from .pagination import CustomPagination
from .premissions import AuthorOrAdmin
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                          FollowSerializer, IngredientsSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserPasswordSerializer)
from food.models import (Favorite, Ingredients, IngredientToRecipe, Recipe,
                         ShoppingCart, Tag)


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
    filter_backends = (DjangoFilterBackend,)
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
    pagination_class = None


class IngredientMixin(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
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

    permission_classes = (IsAuthenticated, )
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


@api_view(['post'])
def set_password(request):
    """Изменить пароль."""

    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль изменен!'},
            status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Введите верные данные!'},
        status=status.HTTP_400_BAD_REQUEST)
