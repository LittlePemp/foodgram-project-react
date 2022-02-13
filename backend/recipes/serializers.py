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
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )

    def get_name(self, obj):
        return obj.ingredients.name

    def get_id(self, obj):
        return obj.ingredients.id

    def get_measurement_unit(self, obj):
        return obj.ingredients.measurement_unit


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
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
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=recipe).exists()

    def validate_name(self, name):
        if not name:
            raise serializers.ValidationError('Название!')
        return name

    def validate_text(self, text):
        if not text:
            raise serializers.ValidationError('Пару слов о реецепте')
        return text

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Из чего готовим?')
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Из чего готовим?')
        return tags

    def create_link_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )

    def create(self, validated_data):
        ingredients = self.validate_ingredients(
            self.initial_data.get('ingredients')
        )
        tags = self.validate_tags(
            self.initial_data.get('tags')
        )
        validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_link_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        recipe = super().update(recipe, validated_data)
        if ingredients:
            recipe.ingredients.clear()
            self.create_link_ingredients(ingredients, recipe)
        if tags:
            recipe.tags.set(tags)
        return recipe


class TargetSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
