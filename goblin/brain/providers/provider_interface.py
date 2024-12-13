from abc import ABC, abstractmethod
from typing import Dict, Any

class ProviderInterface(ABC):
    @abstractmethod
    async def generate_response(self, messages: list[Dict[str, Any]]) -> str:
        """Generate a response based on input messages."""
        pass
