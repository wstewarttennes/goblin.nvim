from langchain_core.runnables import RunnableConfig
from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import BaseMessage
from langchain_community.llms import LlamaCpp
import os
import logging

logger = logging.getLogger(__name__)

class LlamaProvider:
    def __init__(self):
        self.model = LlamaCpp(
            model_path=os.environ.get("LLAMA_MODEL_PATH"),
            temperature=0.75,
            max_tokens=2000,
            n_ctx=2048,
            n_threads=os.cpu_count(),
            streaming=True
        )

    async def generate_response_stream(self, messages: List[BaseMessage]):
        try:
            # Convert messages to prompt
            prompt = "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
            
            # Stream responses
            async for chunk in self.model.astream(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Llama streaming error: {str(e)}")
            raise
