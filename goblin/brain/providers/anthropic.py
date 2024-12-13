from langchain_core.runnables import RunnableConfig
from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import BaseMessage
from langchain_anthropic import ChatAnthropic
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

class AnthropicProvider:
    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
        self.model = ChatAnthropic(
            anthropic_api_key=api_key,
            model_name="claude-3-sonnet-20240229",
            max_tokens=4096,
            streaming=True
        )

    async def generate_response_stream(self, messages: List[BaseMessage]):
        """Generate a streaming response from the model"""
        try:
            async for chunk in self.model.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Anthropic streaming error: {str(e)}")
            raise
