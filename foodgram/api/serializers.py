from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField

from food.models import (Favorite, Ingredients, IngredientToRecipe, Recipe,
                         ShoppingCart, Tag, User)
from users.models import Follow


class UserRegistrationSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'password': {'write_only': True}
        }


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Follow.objects.filter(
            user=user.id,
            author=obj.id).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class IngredientToRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredients.objects.all(),
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.FloatField()

    class Meta:
        model = IngredientToRecipe
        fields = (
            'id',
            'amount',
            'name',
            'measurement_unit',
        )


class ShortResipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True, required=False)
    ingredients = IngredientToRecipeSerializer(
        many=True,
        source='ingredienttorecipe_set'
    )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Готовить из воздуха будете?'
            })

        return data

    def create(self, validated_data):
        request = self.context.get('request', None)
        ingredients = validated_data.pop('ingredienttorecipe_set')
        tags_data = validated_data.pop('tags')
        try:
            recipe = Recipe.objects.create(
                author=request.user,
                **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({
                u'ingredients': 'Что-то прошло не так,'
                u'проверьте веденные данные'
            })
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @staticmethod
    def create_ingredients(recipe, ingredients):
        for ingredient_data in ingredients:
            ingredient_obj = ingredient_data.get('ingredient')
            IngredientToRecipe.objects.create(
                ingredient=ingredient_obj,
                amount=ingredient_data.get('amount'),
                recipe=recipe,
            )

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)

        if 'ingredienttorecipe_set' in validated_data:
            instance.ingredient_recipe.all().delete()
            ingredients_data = validated_data.pop('ingredienttorecipe_set')
            for ingedient in ingredients_data:
                ingedient_instance = ingedient['ingredient']['id']
                ingredient_amount = ingedient['amount']
                IngredientToRecipe.objects.create(
                    recipe=instance,
                    ingredient=ingedient_instance,
                    amount=ingredient_amount
                )
        instance.save()
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    ingredients = IngredientToRecipeSerializer(
        many=True,
        source='ingredienttorecipe_set'
    )
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_tags(self, obj):
        return TagSerializer(
            Tag.objects.filter(recipes=obj),
            many=True,).data

    def get_is_favorited(self, obj):
        request = self.context.get('request', None)
        if request:
            current_user = request.user
        return Favorite.objects.filter(
            user=current_user.id,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request', None)
        if request:
            current_user = request.user
        return ShoppingCart.objects.filter(
            user=current_user.id,
            recipe=obj.id,
        ).exists()

    def validate(self, data):
        all_tag = Tag.objects.all().values_list('id')
        if 'tags' in data:
            tags = data['tags']
            for tag in tags:
                if tag not in all_tag:
                    raise serializers.ValidationError(
                        F'Тега {tag} не существует'
                    )


class FavoriteSerializer(ShortResipeSerializer):
    """Сериализатор избранного"""

    def create(self, validated_data):
        request = self.context.get('request', None)
        current_user = request.user
        current_recipe_id = self.context.get('request').parser_context.get(
            'kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=current_recipe_id)

        try:
            Favorite.objects.create(user=current_user, recipe=recipe)
        except IntegrityError:
            raise serializers.ValidationError({
                'recipe': 'Рецепт уже в избраном'
            })
        return recipe


class FollowSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        if limit:
            queryset = Recipe.objects.filter(
                author=obj).order_by('-id')[:int(limit)]
        else:
            queryset = Recipe.objects.filter(author=obj)

        return ShortResipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def create(self, validated_data):
        request = self.context.get('request', None)
        author_id = self.context.get('request').parser_context.get(
            'kwargs').get('user_id')

        current_user = request.user
        author = get_object_or_404(User, pk=author_id)
        try:
            Follow.objects.create(user=current_user, author=author)
        except IntegrityError:
            raise serializers.ValidationError({
                'author': 'Вы уже подписаны на этого автора'
            })
        return author


class ShoppingCartSerializer(ShortResipeSerializer):
    def create(self, validated_data):
        request = self.context.get('request', None)
        current_user = request.user
        current_recipe_id = self.context.get('request').parser_context.get(
            'kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=current_recipe_id)
        try:
            ShoppingCart.objects.create(user=current_user, recipe=recipe)
        except IntegrityError:
            raise serializers.ValidationError({
                'recipe': 'Рецепт уже в списке покупок'
            })
        return recipe
