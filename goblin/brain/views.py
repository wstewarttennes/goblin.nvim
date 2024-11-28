from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from brain.serializers import GroupSerializer, UserSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from brain.models import TranscriptionSession, AudioChunk
from brain.tasks import process_audio_chunk
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


# Audio Views

class TranscriptionViewSet(viewsets.ViewSet):
    def create(self, request):
        session = TranscriptionSession.objects.create(
            model_name=request.data.get('model_name', 'base')
        )
        return Response({
            'session_id': session.session_id,
            'websocket_url': f'ws://localhost:8000/ws/transcription/{session.session_id}/'
        })

    @action(detail=True, methods=['post'])
    def chunk(self, request, pk=None):
        try:
            session = TranscriptionSession.objects.get(pk=pk)
            if not session.is_active:
                return Response(
                    {'error': 'Session is not active'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            chunk = AudioChunk.objects.create(
                session=session,
                chunk_number=request.data.get('chunk_number'),
                audio_data=base64.b64decode(request.data.get('audio_data'))
            )
            
            process_audio_chunk.delay(chunk.id)
            
            return Response({'status': 'processing'})
            
        except TranscriptionSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        try:
            session = TranscriptionSession.objects.get(pk=pk)
            session.is_active = False
            session.save()
            return Response({'status': 'stopped'})
        except TranscriptionSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
