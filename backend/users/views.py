from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Follow, User
from .paginations import LimitPagination
from .serializers import FollowSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    @action(detail=False, methods=['GET'])
    def me(self, request):
        data = UserSerializer(
            self.request.user,
            context={'request': request}).data
        return Response(data)

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user
        serializer = FollowSerializer(author)
        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response({"errors": "Вы уже подписаны на этого автора"},
                                status=status.HTTP_400_BAD_REQUEST)
            elif author == user:
                return Response({"errors": "Нельзя подписываться на себя"},
                                status=status.HTTP_400_BAD_REQUEST)

            Follow.objects.create(user=user, author=author)
            data = UserSerializer(
                author,
                context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LimitPagination

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
