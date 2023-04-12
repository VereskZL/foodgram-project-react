from django.contrib import admin

from .models import Ingredients, IngredientToRecipe, Recipe, Tag

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredients)
admin.site.register(IngredientToRecipe)
