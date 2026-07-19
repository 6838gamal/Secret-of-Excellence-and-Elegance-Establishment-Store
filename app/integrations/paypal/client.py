"""
PayPal REST API v2 — Orders
Sandbox: https://api-m.sandbox.paypal.com
Production: https://api-m.paypal.com
"""
import httpx
from app.config.settings import settings


class PayPalError(Exception):
    pass


class PayPalClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = (
            "https://api-m.sandbox.paypal.com"
            if settings.PAYPAL_SANDBOX
            else "https://api-m.paypal.com"
        )

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
            )
        if resp.status_code != 200:
            raise PayPalError(f"Cannot get PayPal token: {resp.status_code} — {resp.text}")
        return resp.json()["access_token"]

    async def create_order(
        self,
        order_uuid: str,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        cancel_url: str,
    ) -> dict:
        """Create a PayPal order. Returns full PayPal order object."""
        token = await self._get_access_token()
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": order_uuid,
                    "description": description[:127],
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                }
            ],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "مؤسسة سر التميز والأناقة",
                "locale": "ar-SA",
                "user_action": "PAY_NOW",
            },
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code not in (200, 201):
            raise PayPalError(f"PayPal create order error: {resp.status_code} — {resp.text}")
        return resp.json()

    async def capture_order(self, paypal_order_id: str) -> dict:
        """Capture an approved PayPal order."""
        token = await self._get_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders/{paypal_order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code not in (200, 201):
            raise PayPalError(f"PayPal capture error: {resp.status_code} — {resp.text}")
        return resp.json()


paypal_client = PayPalClient()
