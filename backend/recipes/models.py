from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        verbose_name='Цвет HEX',
    )
    slug = models.SlugField(
        max_length=200,
        blank=True,
        unique=True,
        verbose_name='Cлаг',
    )

    class Meta:
        verbose_name = 'Тег'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes/images/",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
        related_name='ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        verbose_name='Время приготовления (мин.)',
    )

    class Meta:
        verbose_name = 'Рецепт'
        ordering = ('name',)

    def favorites_count(self):
        return self.favorites.count()

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_recipe',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='ingredients_recipe',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Доза',
        validators=(MinValueValidator(1),),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredients'],
                name='ingredients_recipe',
            ),
        ]
        verbose_name = 'Ингредиентов в рецепте'
        ordering = ('recipe',)

    def __str__(self):
        return self.recipe.name


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='favorite',
            ),
        ]
        verbose_name = 'Избранное'
        ordering = ('user',)

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shopping_cart',
            ),
        ]
        verbose_name = 'Корзина'

    def __str__(self):
        return f'{self.user}, {self.recipe}'
