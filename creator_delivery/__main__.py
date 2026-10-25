import os

from .infrai_mail import InfraiMail
from .workflow import DeliveryInput, SubscriberLedger, deliver_asset


def main() -> None:
    recipient = os.environ.get("CREATOR_EMAIL_TO")
    if not recipient:
        raise SystemExit("CREATOR_EMAIL_TO is required")
    outcome = deliver_asset(
        DeliveryInput("order-1001", recipient, "Weekend storefront guide", "https://example.com/download/order-1001"),
        InfraiMail(),
        SubscriberLedger(),
    )
    print(f"{outcome.message_id}: {outcome.subscriber_state}")


if __name__ == "__main__":
    main()
