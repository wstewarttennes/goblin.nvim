# # consumers.py
# import json
# import asyncio
# import backoff
# from anthropic import APIStatusError
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from brain.models import (
#     Conversation, Message, TranscriptionSession, 
#     AudioChunk, Action
# )
# import openai
# from django.conf import settings
# import uuid
# import base64
#
# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
#         self.conversation = await self.create_conversation()
#         await self.send_chat_history()
#
#     async def disconnect(self, close_code):
#         await self.mark_conversation_ended()
#
#     @database_sync_to_async
#     def create_conversation(self):
#         return Conversation.objects.create()
#
#     @database_sync_to_async
#     def mark_conversation_ended(self):
#         if hasattr(self, 'conversation'):
#             self.conversation.is_active = False
#             self.conversation.save()
#
#     @database_sync_to_async
#     def save_message(self, content, role, audio_session=None):
#         return Message.objects.create(
#             conversation=self.conversation,
#             content=content,
#             role=role,
#             audio_session=audio_session
#         )
#
#     @database_sync_to_async
#     def get_chat_history(self):
#         messages = Message.objects.filter(
#             conversation=self.conversation
#         ).order_by('datetime_created')
#         return [
#             {
#                 'role': msg.role,
#                 'content': msg.content,
#                 'timestamp': msg.datetime_created.isoformat(),
#                 'has_audio': bool(msg.audio_session)
#             }
#             for msg in messages
#         ]
#
#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             message_type = data.get('type', 'text')
#
#             handlers = {
#                 'text': self.handle_text_message,
#                 'audio': self.handle_audio_message,
#                 'start_recording': self.handle_start_recording,
#                 'audio_chunk': self.handle_audio_chunk,
#                 'end_recording': self.handle_end_recording
#             }
#
#             handler = handlers.get(message_type)
#             if handler:
#                 await handler(data)
#             else:
#                 await self.send_error('Unknown message type')
#
#         except json.JSONDecodeError:
#             await self.send_error('Invalid message format')
#         except Exception as e:
#             await self.send_error(str(e))
#
#     async def handle_text_message(self, data):
#         message = data.get('message', '').strip()
#         if not message:
#             await self.send_error('Message is required')
#             return
#
#         # Save user message
#         await self.save_message(message, 'user')
#         
#         # Get AI response
#         try:
#             response = await self.get_ai_response(message)
#             await self.save_message(response, 'assistant')
#             
#             await self.send(json.dumps({
#                 'type': 'chat_message',
#                 'role': 'assistant',
#                 'content': response
#             }))
#         except Exception as e:
#             await self.send_error(f'Failed to get AI response: {str(e)}')
#
#     async def handle_start_recording(self, data):
#         self.audio_session = await self.create_audio_session()
#         await self.send(json.dumps({
#             'type': 'recording_started',
#             'session_id': str(self.audio_session.session_id)
#         }))
#
#     @database_sync_to_async
#     def create_audio_session(self):
#         return TranscriptionSession.objects.create()
#
#     async def handle_audio_chunk(self, data):
#         if not hasattr(self, 'audio_session'):
#             await self.send_error('No active recording session')
#             return
#
#         chunk_data = data.get('chunk')
#         chunk_number = data.get('chunk_number')
#         
#         if not chunk_data or chunk_number is None:
#             await self.send_error('Invalid audio chunk data')
#             return
#
#         try:
#             # Decode base64 audio data
#             audio_data = base64.b64decode(chunk_data)
#             
#             # Save chunk
#             await self.save_audio_chunk(chunk_number, audio_data)
#             
#             await self.send(json.dumps({
#                 'type': 'chunk_received',
#                 'chunk_number': chunk_number
#             }))
#         except Exception as e:
#             await self.send_error(f'Failed to process audio chunk: {str(e)}')
#
#     @database_sync_to_async
#     def save_audio_chunk(self, chunk_number, audio_data):
#         return AudioChunk.objects.create(
#             session=self.audio_session,
#             chunk_number=chunk_number,
#             audio_data=audio_data
#         )
#
#     async def handle_end_recording(self, data):
#         if not hasattr(self, 'audio_session'):
#             await self.send_error('No active recording session')
#             return
#
#         try:
#             # Combine all chunks and transcribe
#             chunks = await self.get_audio_chunks()
#             transcription = await self.transcribe_audio(chunks)
#             
#             # Save transcription
#             await self.update_chunks_with_transcription(transcription)
#             
#             # Get AI response for transcription
#             response = await self.get_ai_response(transcription)
#             
#             # Save messages
#             await self.save_message(transcription, 'user', self.audio_session)
#             await self.save_message(response, 'assistant')
#             
#             # Send response to client
#             await self.send(json.dumps({
#                 'type': 'transcription_complete',
#                 'transcription': transcription,
#                 'response': response
#             }))
#             
#             # Clear audio session
#             delattr(self, 'audio_session')
#             
#         except Exception as e:
#             await self.send_error(f'Failed to process recording: {str(e)}')
#
#     @database_sync_to_async
#     def get_audio_chunks(self):
#         return list(AudioChunk.objects.filter(
#             session=self.audio_session
#         ).order_by('chunk_number'))
#
#     async def transcribe_audio(self, chunks):
#         # Combine chunks and transcribe using Whisper
#         try:
#             combined_audio = b''.join(chunk.audio_data for chunk in chunks)
#             
#             # Save temporary file
#             temp_file_path = f'/tmp/{uuid.uuid4()}.wav'
#             with open(temp_file_path, 'wb') as f:
#                 f.write(combined_audio)
#             
#             with open(temp_file_path, 'rb') as audio_file:
#                 transcript = await self.whisper_transcribe(audio_file)
#             
#             return transcript
#             
#         finally:
#             import os
#             if os.path.exists(temp_file_path):
#                 os.remove(temp_file_path)
#
#     async def whisper_transcribe(self, audio_file):
#         loop = asyncio.get_event_loop()
#         response = await loop.run_in_executor(
#             None,
#             lambda: openai.Audio.transcribe("whisper-1", audio_file)
#         )
#         return response.text
#
#     @database_sync_to_async
#     def update_chunks_with_transcription(self, transcription):
#         AudioChunk.objects.filter(session=self.audio_session).update(
#             transcription=transcription,
#             processed=True
#         )
#
#     async def get_ai_response(self, message):
#         loop = asyncio.get_event_loop()
#         try:
#             response = await loop.run_in_executor(
#                 None,
#                 lambda: openai.ChatCompletion.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {"role": "system", "content": "You are Goblin, a helpful AI assistant."},
#                         {"role": "user", "content": message}
#                     ]
#                 )
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             print(f"OpenAI API error: {str(e)}")
#             raise Exception("Failed to get AI response")
#
#     async def send_error(self, message):
#         await self.send(json.dumps({
#             'type': 'error',
#             'message': message
#         }))
#
#
#
