from langchain_core.runnables import RunnableConfig
from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
import os
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider:
    def __init__(self):
        self.model = ChatOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="gpt-4-1106-preview",
            streaming=True
        )

    async def generate_response_stream(self, messages: List[BaseMessage]):
        try:
            # Don't await the astream call directly
            stream = self.model.astream(messages)
            # Instead, iterate over the async generator
            async for chunk in stream:
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise
