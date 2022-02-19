from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.paginations import LimitPagination
from .filters import IngredientFilter, RecipeFilter
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .permissions import IsAuthor, IsReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, TagSerializer, TargetSerializer)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    permission_classes = [AllowAny]
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsReadOnly | IsAuthor,)
    pagination_class = LimitPagination
    filter_backends = [DjangoFilterBackend]
    filter_class = RecipeFilter
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def processing_item(self, request, id, obj):
        item = obj.objects.filter(
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
            obj.objects.create(
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
    def favorite(self, request, id=None):
        response = self.processing_item(
            request=request,
            id=id,
            obj=Favorite,
        )
        return response

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, id=None):
        response = self.processing_item(
            request=request,
            id=id,
            obj=ShoppingCart,
        )
        return response

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by()
        products = [
            (
                f"{ingredient['ingredients__name']}\t --"
                f" {ingredient['total_amount']}\t"
                f"({ingredient['ingredients__measurement_unit']})\n"
            )
            for ingredient in ingredients]
        response = HttpResponse(products, content_type='text/plain')
        attachment = 'attachment; filename="products.txt"'
        response['Content-Disposition'] = attachment
        return response
