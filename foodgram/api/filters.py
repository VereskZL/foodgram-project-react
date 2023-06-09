from django_filters import (ModelMultipleChoiceFilter, NumberFilter,
                            rest_framework)
from food.models import Ingredients, Recipe, Tag
from rest_framework.filters import SearchFilter


class IngredientFilter(SearchFilter):
    search_param = 'name'

    class Meta:
        model = Ingredients
        fields = ('name',)


class MyFilterSet(rest_framework.FilterSet):
    author = rest_framework.NumberFilter(
        field_name='author__id'
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = NumberFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(
        method='filter_shopping_cart')

    def filter_shopping_cart(self, qs, name, value):
        if value == 1:
            return qs.filter(shopping_list__user=self.request.user)

    def filter_is_favorited(self, qs, name, value):
        if value == 1:
            return qs.filter(favorites__user=self.request.user)

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']
