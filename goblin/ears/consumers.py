import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage
import openai
from django.conf import settings
from functools import partial

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Load recent chat history
        history = await self.get_chat_history()
        await self.send(json.dumps({
            'type': 'chat_history',
            'messages': history
        }))

    async def disconnect(self, close_code):
        pass

    @database_sync_to_async
    def save_message(self, user_message, ai_response, is_audio=False, transcript=None):
        """Save messages to database"""
        return ChatMessage.objects.create(
            user_message=user_message,
            ai_response=ai_response,
            is_audio=is_audio,
            transcript=transcript
        )

    @database_sync_to_async
    def get_chat_history(self, limit=50):
        """Get recent chat history"""
        messages = ChatMessage.objects.all()[:limit]
        return [
            {
                'user_message': msg.user_message,
                'ai_response': msg.ai_response,
                'is_audio': msg.is_audio,
                'transcript': msg.transcript,
                'timestamp': msg.created_at.isoformat()
            }
            for msg in messages
        ]

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'text')
            
            if message_type == 'text':
                message = data.get('message', '')
                if not message:
                    raise ValueError('Message is required')
                
                # Get AI response
                response = await self.get_ai_response(message)
                
                # Save to database
                await self.save_message(message, response)
                
                # Send response
                await self.send(json.dumps({
                    'type': 'chat_message',
                    'user_message': message,
                    'ai_response': response
                }))
                
            elif message_type == 'audio_transcription':
                transcript = data.get('transcript', '')
                if not transcript:
                    raise ValueError('Transcript is required')
                
                # Get AI response for transcript
                response = await self.get_ai_response(transcript)
                
                # Save to database
                await self.save_message(
                    transcript, 
                    response,
                    is_audio=True,
                    transcript=transcript
                )
                
                # Send response
                await self.send(json.dumps({
                    'type': 'chat_message',
                    'user_message': transcript,
                    'ai_response': response,
                    'is_audio': True
                }))

        except json.JSONDecodeError:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def get_ai_response(self, message):
        """Get response from OpenAI"""
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                partial(
                    openai.ChatCompletion.create,
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are Goblin, a helpful AI assistant."},
                        {"role": "user", "content": message}
                    ],
                    api_key=settings.OPENAI_API_KEY
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise Exception("Failed to get AI response")

