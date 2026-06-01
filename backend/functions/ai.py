from backend.settings import settings
from typing import Union

class FakeAIProvider:
    async def AnalyzeMessage(self, text: str, conversation: dict) -> dict:
        pass

class OpenAIProvider:
    async def AnalyzeMessage(self, text: str, conversation: dict) -> dict:
        return {
            "provider": "openai",
            "mode": "not_implemented_yet",
            "intent": None,
            "speciality": None,
            "period": None,
            "should_handoff": False,
            "confidence": 0,
        }

class AIInterpreter:
    def __init__(self, provider: Union[FakeAIProvider, OpenAIProvider]):
        self.provider = provider

    async def InterpretMessage(self, text: str, conversation: dict) -> dict:
        return await self.provider.AnalyzeMessage(text, conversation)
    
if settings.AI_MODE == "OpenAI":
    ai_provider = OpenAIProvider()
else:
    ai_provider = FakeAIProvider()

ai = AIInterpreter(provider=ai_provider)