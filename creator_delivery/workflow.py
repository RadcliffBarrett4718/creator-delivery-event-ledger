from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .infrai_mail import InfraiMail


@dataclass(frozen=True)
class DeliveryInput:
    order_id: str
    subscriber_email: str
    asset_name: str
    download_url: str


@dataclass(frozen=True)
class DeliveryOutcome:
    message_id: str
    subscriber_state: str


class ContentProcessor:
    def render(self, item: DeliveryInput) -> str:
        return (
            f"<h1>Your {item.asset_name} is ready</h1>"
            f"<p>Order {item.order_id}: <a href=\"{item.download_url}\">download your file</a>.</p>"
        )


class SubscriberLedger:
    def __init__(self) -> None:
        self.states: dict[str, str] = {}

    def apply_events(self, email: str, events: list[dict[str, Any]]) -> str:
        names = {str(event.get("type", event.get("event", ""))).lower() for event in events}
        state = "bounced" if "bounce" in names else "engaged" if "open" in names else "sent"
        self.states[email] = state
        return state


def deliver_asset(item: DeliveryInput, mail: InfraiMail, ledger: SubscriberLedger) -> DeliveryOutcome:
    message = mail.send(
        item.subscriber_email,
        f"Your {item.asset_name} delivery",
        ContentProcessor().render(item),
        request_id=f"delivery-{item.order_id}",
    )
    state = ledger.apply_events(item.subscriber_email, mail.events(message.message_id))
    return DeliveryOutcome(message.message_id, state)
