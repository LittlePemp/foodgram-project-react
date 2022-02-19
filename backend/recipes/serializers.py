from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredients.id')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
    )
    ingredients = RecipeIngredientSerializer(
        source='ingredients_recipe',
        read_only=True,
        many=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'ingredients',
            'cooking_time',
            'tags',
            'image',
            'is_in_shopping_cart',
            'is_favorited',
            'author',
        )
        read_only_fields = (
            'id',
            'author',
        )

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_authenticated and Favorite.objects.filter(user=user,
                                                             recipe=recipe
                                                             ).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if (user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=recipe).exists()):
            return True
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientCreateSerializer(
        source='ingredients_recipe',
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'ingredients',
            'cooking_time',
            'tags',
            'image'
        )

    def validate_name(self, name):
        if not name:
            raise serializers.ValidationError('Название!')
        return name

    def validate_text(self, text):
        if not text:
            raise serializers.ValidationError('Пару слов о реецепте')
        return text

    def validate_tags(self, tags):
        if (not tags) or (len(tags) != len(set(tags))):
            raise serializers.ValidationError('Теги!')
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Из чего готовим?')
        unique_check = list()
        for ingredient in ingredients:
            ingredient_id = ingredient.get('ingredients').get('id')
            if ((ingredient_id not in unique_check)
                and get_object_or_404(Ingredient,
                                      id=ingredient_id)):
                unique_check.append(ingredient_id)
            else:
                raise serializers.ValidationError('Проверьте id ингредиентов')
        return ingredients

    def validate_cooking_time(self, cooking_time):
        if not cooking_time:
            raise serializers.ValidationError('Время - деньги!')
        return cooking_time

    def create_link_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients_id=ingredient.get('ingredients').get('id'),
                amount=ingredient.get('amount'),
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients_recipe')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_link_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients_recipe')
        tags = validated_data.pop('tags')
        recipe = super().update(recipe, validated_data)
        recipe.ingredients.clear()
        self.create_link_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe


class TargetSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'name',
            'image',
            'cooking_time',
        )
