import httpx
from backend.settings import settings
from typing import Union

class FakeProvider:
    def Send(self, to: str, text: str) -> dict:
        return {
            "provider": "fake_whatsapp",
            "to": to,
            "type": "text",
            "text": text,
            "status": "sent_fake",
        }
    
class CloudProvider:
    def BuildTextPayload(self, to: str, text: str) -> dict:
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": text,
            }
        }

    async def Send(self, to: str, text: str) -> dict:
        payload = self.BuildTextPayload(to, text)
        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.PHONE_NUMBER_ID}/messages"

        if settings.WHATSAPP_DRY_RUN:
            return {
                "provider": "whatsapp_cloud_api",
                "mode": "dry_run",
                "method": "POST",
                "url": url,
                "payload": payload,
                "status": "not_sent_dry_run",
            }
        
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)

        try:
            response_body = response.json()
        except:
            response_body = response.text

        return {
            "provider": "whatsapp_cloud_api",
            "mode": "live",
            "method": "POST",
            "url": url,
            "status_code": response.status_code,
            "response": response_body,
        }

    
class WhatsAppSender:
    def __init__(self, provider: Union[FakeProvider, CloudProvider]):
        self.provider = provider

    def SendTextMessage(self, to: str, text: str) -> dict:
        return self.provider.Send(to, text)
    
if settings.WHATSAPP_MODE == "Cloud":
    provider = CloudProvider()
else:
    provider = FakeProvider()

sender = WhatsAppSender(provider=provider)