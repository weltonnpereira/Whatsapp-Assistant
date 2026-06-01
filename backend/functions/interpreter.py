import json
import os

from backend.functions.ai import ai
from backend.functions.chat import Auxiliary

class RuleInterpreter:
    _JSON_PATH = os.path.join("backend", "packets", "wordlists.json")
    _WORDLISTS = None

    @classmethod
    def GetWordlists(cls) -> dict:
        if cls._WORDLISTS is None:
            try:
                with open(cls._JSON_PATH, "r", encoding="utf-8") as file:
                    cls._WORDLISTS = json.load(file).get("chat", {})
            except Exception as e:
                print(f"Error loading wordlists: {e}")
                cls._WORDLISTS = {}
        return cls._WORDLISTS
    
    @classmethod
    def DetectIntent(cls, text: str) -> str:
        text_lower = text.lower()

        for intent, keywords in cls.GetWordlists().items():
            if any(word in text_lower for word in keywords):
                return intent
            
        return "unknown"
    
    @classmethod
    def Interpret(cls, text: str, conversation: dict) -> dict:
        intent = cls.DetectIntent(text)

        return {
            "source": "rules",
            "intent": intent,
            "speciality": Auxiliary.NormalizeSpeciality(text),
            "period": Auxiliary.NormalizePeriod(text),
            "should_handoff": intent == "human",
            "confidence": 0.9 if intent != "unknown" else 0.3,
        }
    
class HybridInterpreter:
    @staticmethod
    async def Interpret(text: str, conversation: dict) -> dict:
        rule_analysis = RuleInterpreter.Interpret(text, conversation)

        if rule_analysis["confidence"] >= 0.8:
            return rule_analysis
        
        ai_analysis = await ai.InterpretMessage(text, conversation)

        if ai_analysis and ai_analysis.get("confidence", 0) > rule_analysis["confidence"]:
            return ai_analysis
        
        return rule_analysis