"""
Moyasar Payment Gateway
Docs: https://docs.moyasar.com
API Base: https://api.moyasar.com/v1
Amount unit: smallest (halalas for SAR — 1 SAR = 100 halalas)
"""
import base64
import hashlib
import hmac
import httpx
from app.config.settings import settings


class MoyasarError(Exception):
    pass


class MoyasarClient:
    BASE_URL = "https://api.moyasar.com/v1"

    def __init__(self):
        self.publishable_key = settings.MOYASAR_PUBLISHABLE_KEY
        self.secret_key = settings.MOYASAR_SECRET_KEY

    @property
    def configured(self) -> bool:
        return bool(self.publishable_key)

    def _auth_headers(self) -> dict:
        creds = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        return {
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def to_halalas(amount: float, currency: str) -> int:
        """Convert major unit to smallest unit (halalas for SAR, fils for others)."""
        zero_decimal = {"KWD", "BHD", "OMR"}   # 3 decimal places → multiply by 1000
        if currency in zero_decimal:
            return int(round(amount * 1000))
        return int(round(amount * 100))

    async def get_payment(self, payment_id: str) -> dict:
        """Fetch a payment by ID to verify status."""
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{self.BASE_URL}/payments/{payment_id}",
                headers=self._auth_headers(),
            )
        if resp.status_code != 200:
            raise MoyasarError(f"Moyasar get payment error: {resp.status_code} — {resp.text}")
        return resp.json()


moyasar_client = MoyasarClient()
