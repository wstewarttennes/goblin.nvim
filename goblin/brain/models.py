from django.db import models
import uuid

# Create your models here.

class GoblinModel(models.Model):
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)


class Goblin(GoblinModel):

    name = models.CharField(max_length=200)
    description = models.TextField()


class Routine(GoblinModel):

    name = models.CharField(max_length=200)
    description = models.TextField()



# Audio Transcription Models

class TranscriptionSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    model_name = models.CharField(max_length=50, default='base')

    def __str__(self):
        return f"Session {self.session_id} ({self.created_at})"


class AudioChunk(models.Model):
    session = models.ForeignKey(TranscriptionSession, on_delete=models.CASCADE)
    chunk_number = models.IntegerField()
    audio_data = models.BinaryField()
    transcription = models.TextField(null=True, blank=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['chunk_number']
        
    def __str__(self):
        return f"Chunk {self.chunk_number} of Session {self.session.session_id}"


class Conversation(GoblinModel):
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return f"Conversation {self.title or self.session_id}"


class Message(GoblinModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    role = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ])
    audio_session = models.ForeignKey(
        'ears.TranscriptionSession', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['datetime_created']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."




