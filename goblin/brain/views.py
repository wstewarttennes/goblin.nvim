from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from brain.serializers import GroupSerializer, UserSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from brain.models import TranscriptionSession, AudioChunk
import base64


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

