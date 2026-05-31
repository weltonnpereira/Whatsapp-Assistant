from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

from backend.functions.chat import Chat, Auxiliary
from backend.functions.api import sender
from backend.settings import settings

from backend.models import ChatModel

app = FastAPI()

@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.TOKEN:
        return hub_challenge
    
    raise HTTPException(status_code=403, detail="Invalid token")

@app.post("/webhook")   
async def receive_webhook(request: Request):
    payload = await request.json()
    
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok", "message": "none message receive"}
        
        message: dict = messages[0]
        message_id = message.get("id")
        phone = message["from"]
        text = message.get("text", {}).get("body", "")

        if message_id and ChatModel.HasProcessedMessage(message_id):
            return {
                "status": "ok",
                "duplicated": True,
                "message_id": message_id,
            }
        
        if message_id:
            ChatModel.MarkMessageAsProcessed(message_id)

        chat_result = Chat.BuildRobotReply(ChatModel.GetConversations(), phone, text)
        reply = chat_result["reply"]
        action = chat_result["action"]
        send_result = sender.SendTextMessage(phone, reply)

        conversation = ChatModel.GetConversations().get(phone, {})

        print(f"{phone} message: {text}")
        print(f"secretary reply: {reply}")

        lead = None
        if action == "create_lead":
            lead = Auxiliary.BuildLeadSummary(phone, conversation)
            ChatModel.SaveLead(lead)

        return {
            "status": "ok",
            "message_id": message_id,
            "duplicated": False,
            "from": phone,
            "text": text,
            "reply": reply,
            "action": action,
            "lead": lead,
            "send_result": send_result
        }
    except Exception as e:
        print("Error in processing webhook", e)
        return {"status": "ignored"}
    
@app.get("/leads")
async def list_leads():
    return {
        "leads": ChatModel.GetLeads()
    }