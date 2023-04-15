from django.contrib import admin

from . import models


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


@admin.register(models.Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientToRecipeInLine(admin.TabularInline):
    model = models.IngredientToRecipe
    min_num = 1


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name',)
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientToRecipeInLine,)


@admin.register(models.Favorite)
class Favorite(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')


@admin.register(models.ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
