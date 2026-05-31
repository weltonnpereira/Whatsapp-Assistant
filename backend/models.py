CONVERSATIONS: dict = {}
LEADS: list[dict] = []
PROCESSED_MESSAGES: set[str] = set()

FAKE_SCHEDULE: dict = {
    "dermatologista": {
        "manha": ["Segunda 09:00", "Terça 10:30"],
        "tarde": ["Terça 14:00", "Quarta 16:00"],
    },
    "dentista": {
        "manha": ["Segunda 08:30", "Quarta 11:00"],
        "tarde": ["Quinta 15:00", "Sexta 17:00"],
    },
}

class ChatModel():
    # para isso ser escalavel teriamos que ao colocar um crm criar um sistema rapido para
    # identificar os leads duplicados sem travar o banco de dados passando por milhoes de leads (fazer mais para frente)
    def SaveLead(lead: dict) -> dict:
        for existing_lead in LEADS:
            same_phone = existing_lead.get("phone") == lead.get("phone")
            same_slot = existing_lead.get("selected_slot") == lead.get("selected_slot")

            if same_phone and same_slot:
                return existing_lead

        LEADS.append(lead)
        return lead

    def GetConversations():
        return CONVERSATIONS

    def GetSchedule():
        return FAKE_SCHEDULE

    def GetLeads():
        return LEADS
    
    def HasProcessedMessage(message_id: str) -> bool:
        return message_id in PROCESSED_MESSAGES
    
    def MarkMessageAsProcessed(message_id: str):
        PROCESSED_MESSAGES.add(message_id)