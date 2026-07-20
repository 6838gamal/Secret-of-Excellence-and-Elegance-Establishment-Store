"""
Moyasar Payment Gateway
Docs: https://docs.moyasar.com
API Base: https://api.moyasar.com/v1/payments
Amount unit: smallest (halalas for SAR — 1 SAR = 100 halalas)

Auth: Basic Auth — secret key as username, empty password
  requests.get(url, auth=('sk_test_...', ''))
"""
import httpx
from app.config.settings import settings


class MoyasarError(Exception):
    pass


class MoyasarClient:
    BASE_URL = "https://api.moyasar.com/v1/payments"

    def __init__(self):
        self.publishable_key = settings.MOYASAR_PUBLISHABLE_KEY
        self.secret_key = settings.MOYASAR_SECRET_KEY

    @property
    def configured(self) -> bool:
        return bool(self.publishable_key)

    def _auth(self) -> tuple:
        """Basic Auth: (secret_key, '') — as per Moyasar docs."""
        return (self.secret_key or "", "")

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
                f"{self.BASE_URL}/{payment_id}",
                auth=self._auth(),
            )
        if resp.status_code != 200:
            raise MoyasarError(f"Moyasar get payment error: {resp.status_code} — {resp.text}")
        return resp.json()


moyasar_client = MoyasarClient()
