import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from creator_delivery.infrai_mail import MailResult
from creator_delivery.workflow import DeliveryInput, SubscriberLedger, deliver_asset


class FakeMail:
    def send(self, to, subject, body, request_id):
        assert to == "buyer@example.com"
        assert "download" in body
        assert request_id == "delivery-order-7"
        return MailResult("message-7")

    def events(self, message_id):
        assert message_id == "message-7"
        return [{"type": "open"}]


def test_opened_delivery_marks_subscriber_engaged():
    ledger = SubscriberLedger()
    result = deliver_asset(
        DeliveryInput("order-7", "buyer@example.com", "Pattern pack", "https://example.com/file"),
        FakeMail(),
        ledger,
    )
    assert result.subscriber_state == "engaged"
    assert ledger.states["buyer@example.com"] == "engaged"


def test_bounce_takes_priority_over_open():
    ledger = SubscriberLedger()
    assert ledger.apply_events("buyer@example.com", [{"type": "open"}, {"type": "bounce"}]) == "bounced"
