from django.urls import path, include
from brain import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'groups', views.GroupViewSet, basename='groups')
router.register(r'transcription', views.TranscriptionViewSet, basename='transcription')


urlpatterns = [
    path("", include(router.urls)),
    path("", views.index, name="index"),
]

