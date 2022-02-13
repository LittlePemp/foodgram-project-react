from django.urls import include, path
from rest_framework import routers

from users.views import UserViewSet, SubscriptionListView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename="users")

urlpatterns = [
    path('users/subscriptions/', SubscriptionListView.as_view()),
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
