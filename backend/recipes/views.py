from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.paginations import LimitPagination

from .filters import IngredientFilter, RecipeFilter
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .permissions import IsAuthor, IsReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          TagSerializer, TargetSerializer)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsReadOnly | IsAuthor,)
    pagination_class = LimitPagination
    filter_backend = (RecipeFilter,)
    lookup_field = 'id'

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, id=None):
        item = Favorite.objects.filter(
            user=request.user,
            recipe__id=id,
        )
        msg = ('Только POST запрос на существующий,',
               'DELETE на несуществующий рецепт')
        if (request.method == 'POST') and (not item.exists()):
            recipe = get_object_or_404(
                Recipe,
                id=id,
            )
            Favorite.objects.create(
                user=request.user,
                recipe=recipe,
            )
            serializer = TargetSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif (request.method == 'DELETE') and (item.exists()):
            item.delete()
            msg = 'Удалено'
            return Response(
                {'Confirmation': msg},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': msg},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, id=None):
        item = ShoppingCart.objects.filter(
            user=request.user,
            recipe__id=id,
        )
        msg = ('Только POST запрос на существующий,',
               'DELETE на несуществующий рецепт')
        if (request.method == 'POST') and (not item.exists()):
            recipe = get_object_or_404(
                Recipe,
                id=id,
            )
            ShoppingCart.objects.create(
                user=request.user,
                recipe=recipe,
            )
            serializer = TargetSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif (request.method == 'DELETE') and (item.exists()):
            item.delete()
            msg = 'Удалено'
            return Response(
                {'Confirmation': msg},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': msg},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        products = [
            (
                f"{ingredient['ingredients__name']}\t"
                f" {ingredient['total_amount']}\n"
                f" ({ingredient['ingredients__measurement_unit']})\t"
            )
            for ingredient in ingredients]
        response = HttpResponse(products, content_type='text/plain')
        attachment = 'attachment; filename="products.txt"'
        response['Content-Disposition'] = attachment
        return response
