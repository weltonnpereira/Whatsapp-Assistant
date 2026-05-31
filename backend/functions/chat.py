import json
import os
from backend.models import ChatModel

class Auxiliary():
    @staticmethod
    def NormalizeSpeciality(text: str) -> str:
        text_lower = text.lower()

        if "dermato" in text_lower:
            return "dermatologista"
        
        if "dente" in text_lower or "dentista" in text_lower or "odonto" in text_lower:
            return "dentista"
        
        return text_lower.strip()
    
    @staticmethod
    def NormalizePeriod(text: str) -> str:
        text_lower = text.lower()

        if "manha" in text_lower or "manhã" in text_lower:
            return "manha"
        
        if "tarde" in text_lower:
            return "tarde"
        
        return text_lower.strip()
    
    @staticmethod
    def MatchSelectedSlot(text: str, available_slots: list[str]) -> str | None:
        text_lower = text.lower()

        for slot in available_slots:
            slot_lower = slot.lower()

            if text_lower == slot_lower:
                return slot
            
            if text_lower in slot_lower:
                return slot
            
        return None
    
    @staticmethod
    def BuildLeadSummary(phone: str, conversation: dict) -> dict:
        return {
            "phone": phone,
            "name": conversation.get("name"),
            "speciality": conversation.get("speciality"),
            "period": conversation.get("period"),
            "selected_slot": conversation.get("selected_slot"),
            "status": conversation.get("step"),
        }
    
    @staticmethod
    def BuildChatResult(reply: str, action: str = "continue_conversation") -> dict:
        return {
            "reply": reply,
            "action": action
        }

class Chat(Auxiliary):
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

    @staticmethod
    def FindAvailableSlots(speciality: str, period: str) -> list[str]:
        speciality_key = speciality.lower().strip()
        period_key = period.lower().strip()

        speciality_schedule: dict = ChatModel.GetSchedule().get(speciality_key)

        if not speciality_schedule:
            return []
        
        return speciality_schedule.get(period_key, [])

    @classmethod
    def BuildRobotReply(cls, conversations: dict, phone: str, text: str) -> dict:
        conversation = conversations.get(phone, {"step": "new"})
        intent = cls.DetectIntent(text)

        if conversation["step"] == "new":
            if intent == "schedule":
                conversations[phone] = {"step": "asking_speciality"}
                return cls.BuildChatResult(
                    "Olá! Posso te ajudar com o agendamento. Qual especialidade você procura?"
                )

            if intent == "price":
                return cls.BuildChatResult(
                    "Claro. Para te passar a informação correta, qual procedimento ou especialidade você procura?"
                )
            
            if intent == "human":
                return cls.BuildChatResult(
                    "Certo, vou te encaminhar para uma atendente.",
                    "handoff_to_human"
                )
            
            return cls.BuildChatResult(
                "Olá! Sou a assistente virtual da clínica. Você quer agendar uma consulta, saber valores ou falar com uma atendente?"
            )
        
        # reset
        if intent == "reset":
            conversations[phone] = {"step": "asking_speciality"}
            return cls.BuildChatResult(
                "Claro, vamos começar um novo agendamento. Qual especialidade você procura?"
            )
        
        if conversation["step"] == "asking_speciality":
            conversation["speciality"] = cls.NormalizeSpeciality(text)
            conversation["step"] = "asking_period"
            conversations[phone] = conversation
            return cls.BuildChatResult(
                "Perfeito. Você prefere atendimento de manhã ou à tarde?"
            )
        
        if conversation["step"] == "asking_period":
            conversation["period"] = cls.NormalizePeriod(text)
            
            slots = cls.FindAvailableSlots(
                conversation["speciality"],
                conversation["period"]
            )

            if not slots:
                conversation["step"] = "asking_period"
                conversations[phone] = conversation
                return cls.BuildChatResult(
                    "Não encontrei horários para essa especialidade nesse período. Você prefere manhã ou tarde?"
                )
            
            conversation["available_slots"] = slots
            conversation["step"] = "offering_slots"
            conversations[phone] = conversation

            slots_text = " ou ".join(slots)
            return cls.BuildChatResult(
                f"Tenho estes horários disponíveis: {slots_text}. Qual você prefere?"  
            )
        
        if conversation["step"] == "offering_slots":
            selected_slot = cls.MatchSelectedSlot(
                text,
                conversation.get("available_slots", [])
            )

            if not selected_slot:
                slots_text = " ou ".join(conversation.get("available_slots", []))
                return cls.BuildChatResult(
                    f"Não encontrei esse horário nas opções. Você prefere {slots_text}?"
                )
            
            conversation["selected_slot"] = selected_slot
            conversation["step"] = "asking_name"
            conversations[phone] = conversation
            return cls.BuildChatResult(
                f"Perfeito, separei {selected_slot}. Para finalizar a pré-reserva, qual é o seu nome?" 
            )
        
        # Quando o step for scheduled quer dizer que o cliente fez um agendamento ou seja
        # é a hora onde guardamos essa info no crm para utiliza-la depois fazendo um storage e criando um listener
        # que dispara quando chega no dia da consulta ou 1 dia antes para o cliente não esquecer (fazer isso mais para frente)
        if conversation["step"] == "asking_name":
            conversation["name"] = text.strip()
            conversation["step"] = "scheduled"
            conversations[phone] = conversation

            return cls.BuildChatResult(
                (
                    f"Agendamento pré-reservado para {conversation['name']} "
                    f"em {conversation['selected_slot']}. "
                    "Uma atendente irá confirmar seus dados em instantes."
                ),
                "create_lead"
            )

        return cls.BuildChatResult(
            "Seu atendimento já está em andamento. Se quiser, posso chamar uma atendente."
        )