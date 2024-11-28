from brain.agents.developer_one.developer_one import DeveloperOne
from celery import shared_task
from brain.helpers.linear_api import LinearApi
import whisper
import numpy as np
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import tempfile


@shared_task
def check_tasks():
    print('testing')
    print('hello?')

# This is the main entrypoint for brain working on it's own. This task runs every minute and checks for any work that needs to be done
@shared_task
def ping_brain():
    agent_data = {
        # These are used as context
        "codebase_path": "~/dev/ftf",
        "documentation_url": "https://cityflavor.com/schema/swagger-ui/",
        "testing_commands": "python manage.py test",
        "additional_buffer": "",
        # This is the actual thing to build
        "prompt": "Build a modal on the portal home page that allows. ",
    }
    agent = DeveloperOne(agent_data)

    # Find Linear Tickets
    linear_api = LinearApi()
    issues = linear_api.get_issues(filters={
        "label": { "name": "Goblin" },
    })


    for issue in issues:
        ticket_name = issue["name"]
        ticket_description = issue["description"] 
        agent.run()




@shared_task
def process_audio_chunk(chunk_id):
    from .models import AudioChunk
    
    chunk = AudioChunk.objects.get(id=chunk_id)
    model = whisper.load_model(chunk.session.model_name)
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
        temp_file.write(chunk.audio_data)
        temp_file.flush()
        
        result = model.transcribe(temp_file.name)
        
        chunk.transcription = result['text']
        chunk.processed = True
        chunk.save()
        
        # Send result via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'transcription_{chunk.session.session_id}',
            {
                'type': 'transcription_message',
                'message': {
                    'chunk_number': chunk.chunk_number,
                    'transcription': result['text']
                }
            }
        )
