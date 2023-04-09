from django.contrib import admin

from .models import Recipe, Tag, Ingredients, IngredientToRecipe

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredients)
admin.site.register(IngredientToRecipe)
