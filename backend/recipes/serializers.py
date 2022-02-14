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

    def validate_tags(self, tags):
        if (not tags) or (len(tags) != len(set(tags))):
            raise serializers.ValidationError('Теги!')
        return tags

    def validate_cooking_time(self, cooking_time):
        if not cooking_time:
            raise serializers.ValidationError('Время - деньги!')
        return cooking_time

    def validate(self, data):
        """ Удалю потом, просто хочу сказать, что после 6 часов раздумий
        я только так смог засунуть ингредиенты в validated_data.
        Неплохо же вышло))) ;0 """
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Из чего готовим?')
        data['ingredients'] = list()
        for ingredient in ingredients:
            try:
                instance = Ingredient.objects.get(id=ingredient.get('id'))
            except Exception as error:
                raise serializers.ValidationError(
                    f'{error} / Таких ингредиентов еще не изобрели('
                )
            amount = ingredient.get('amount', 0)
            if (not amount) or (amount <= 0):
                raise serializers.ValidationError('Нужна доза')
            data['ingredients'].append(
                {
                    "ingredient": instance,
                    "amount": amount,
                }
            )
        return data

    def create_link_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients=ingredient['ingredient'],
                amount=ingredient['amount'],
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_link_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
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
