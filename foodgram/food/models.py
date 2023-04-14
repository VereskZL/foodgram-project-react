from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Tag(models.Model):
    """ Filter recipe. """

    name = models.CharField(
        max_length=64,
        verbose_name='Название тега'
    )
    color = models.CharField(
        max_length=7,
        verbose_name='Цвет тега')
    slug = models.SlugField(
        verbose_name='Унигальный slug тега',
        unique=True
    )

    def __str__(self):
        return self.name


class Ingredients(models.Model):

    name = models.CharField(
        max_length=64,
        verbose_name='Название ингидиента'
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=32
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Model about recipe. """

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientToRecipe',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='app/',
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message='Не менее одной минуты'),
            MaxValueValidator(1440, message='Не долше 24 часов'),
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True,
    )

    class Meta:
        verbose_name = ("Рецепты")
        constraints = [
            UniqueConstraint(
                fields=('name', 'author'),
                name='unique_recipe_to_author'
            ),
        ]

    def __str__(self):
        return self.name


class IngredientToRecipe(models.Model):
    """ Model wish unit and quantity ingrediens. """

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()

    def __str__(self):
        return (f'{self.ingredient} для {self.recipe}')


class Favorite(models.Model):
    """ Favorite recipe. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_favorite_unique'
            )
        ]
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return (f'Избранный рецепт {self.recipe.name}',
                f'пользователя: {self.user.get_username}')


class ShoppingCart(models.Model):
    """ Model shop list. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_list',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_list',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_shopping_unique'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return (f'Рецепт {self.recipe.name} в списке покупок',
                f' пользователя: {self.user.get_username}')
