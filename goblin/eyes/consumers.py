# eyes/consumers.py
import json
import base64
import logging
from io import BytesIO
from PIL import Image
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

logger = logging.getLogger(__name__)

class ScreenshotConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.claude_client = ChatAnthropic(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("AI_MODEL", "claude-3-opus-20240229")
        )
        self.current_project = None

    async def connect(self):
        """Handle WebSocket connection setup"""
        try:
            await self.accept()
            await self.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected'
            }))
            logger.info(f"WebSocket connection established: {self.channel_name}")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            
            if data['type'] == 'screenshot':
                # Log receipt of screenshot
                logger.info(f"Received screenshot data. Size: {len(data['data']) // 1024}KB Project: {data.get('project')} Timestamp: {data['timestamp']}")
                
                # Process the screenshot
                screenshot_data = data['data']
                timestamp = data['timestamp']
                project = data.get('project', 'default')
                
                try:
                    # Remove the data URL prefix to get just the base64 data
                    if ',' in screenshot_data:
                        base64_data = screenshot_data.split(',')[1]
                    else:
                        base64_data = screenshot_data
                    
                    # Log processing stages
                    logger.info(f"Processing screenshot for project {project}")
                    
                    # Convert base64 to image
                    image_data = base64.b64decode(base64_data)
                    image = Image.open(BytesIO(image_data))
                    
                    # Log the image size
                    logger.info(f"Image processed. Size: {image.size}")
                    
                    # Analyze the screenshot with Claude
                    analysis_result = await self.analyze_screenshot(image, timestamp, project)
                    
                    # Send back the analysis
                    await self.send(json.dumps({
                        'type': 'screenshot_analysis',
                        'analysis': analysis_result,
                        'timestamp': timestamp,
                        'project': project
                    }))
                    logger.info(f"Analysis sent back for screenshot at {timestamp}")
                    
                except Exception as e:
                    logger.error(f"Error processing screenshot: {str(e)}", exc_info=True)
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': f"Error processing screenshot: {str(e)}"
                    }))
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def analyze_screenshot(self, image, timestamp, project):
        """Analyze screenshot using Claude"""
        try:
            print("Analyzing screenshot")
            # Convert image to base64 for Claude
            buffered = BytesIO()
            image.save(buffered, format="JPEG")

            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Create message for Claude with the image and project context
            messages = [
                HumanMessage(content=[
                    {
                        "type": "text",
                        "text": f"""
                            Please look at this screenshot for and provide insights about the content. 
                            Look for any important information, text, or visual elements.
                            Make note of any glaring mistakes you see, whether that be code or something else.
                            Keep responses short and to the point as if you're texting a friend.
                            {'Project: ' + project if project else ""}
                        """
                    },
                    {
                        "type": "image",
                        "source": {  
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_base64
                        }
                    }
                ])
            ]
            
            # Get Claude's analysis
            response = await self.claude_client.ainvoke(messages)
            print('got a response')
            return response.content
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot: {str(e)}", exc_info=True)
            return f"Error analyzing screenshot: {str(e)}"
