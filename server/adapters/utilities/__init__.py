"""Call-Before-You-Dig provider (811 in the US, DT-DICT guichet unique in France).
Sandbox: returns a clearly SIMULATED receipt. Nothing is sent to any real operator."""
import uuid
from datetime import datetime, timedelta, timezone


class SandboxProvider:
    def submit_alert(self, *, ticket_ref: str, lat: float, lng: float, provider: str,
                     response_days: int, valid_months: int = 3) -> dict:
        now = datetime.now(timezone.utc)
        return {
            'provider': provider, 'alert_ref': f'SIM-{uuid.uuid4().hex[:10].upper()}', 'simulated': True,
            'operators': {'notified': [], 'responses_due': (now + timedelta(days=response_days)).isoformat()},
            'valid_until': now + timedelta(days=30 * valid_months),
        }


def get_provider():
    return SandboxProvider()
