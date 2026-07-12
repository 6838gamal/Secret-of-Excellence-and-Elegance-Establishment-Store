"""
Beezati Payment Gateway Integration
Docs: https://docs.beezati.com  (placeholder — update with real endpoints)
"""
import hashlib
import hmac
import json
import httpx
from typing import Optional
from app.config.settings import settings


class BeezatiError(Exception):
    pass


class BeezatiClient:
    def __init__(self):
        self.api_key = settings.BEEZATI_API_KEY
        self.secret = settings.BEEZATI_SECRET
        self.base_url = settings.BEEZATI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_payment(
        self,
        order_uuid: str,
        amount: float,
        currency: str,
        description: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        success_url: str,
        failed_url: str,
        webhook_url: str,
    ) -> dict:
        """
        Create a payment session with Beezati.
        Returns: { payment_url, transaction_id, ... }
        """
        payload = {
            "order_id": order_uuid,
            "amount": amount,
            "currency": currency,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "phone": customer_phone,
            },
            "redirect_urls": {
                "success": success_url,
                "failed": failed_url,
            },
            "webhook_url": webhook_url,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/payments/create",
                json=payload,
                headers=self.headers,
            )

        if response.status_code not in (200, 201):
            raise BeezatiError(f"Beezati API error: {response.status_code} — {response.text}")

        return response.json()

    async def verify_payment(self, transaction_id: str) -> dict:
        """Verify payment status from Beezati."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/payments/{transaction_id}",
                headers=self.headers,
            )

        if response.status_code != 200:
            raise BeezatiError(f"Beezati verify error: {response.status_code}")

        return response.json()

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """HMAC-SHA256 signature verification for webhooks."""
        if not settings.BEEZATI_WEBHOOK_SECRET:
            return True  # Skip if not configured

        expected = hmac.new(
            settings.BEEZATI_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature or "")


beezati_client = BeezatiClient()
