from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UdharViewSet

router = DefaultRouter()
router.register(r'', UdharViewSet, basename='udhar')

urlpatterns = [
    path('', include(router.urls)),
]
