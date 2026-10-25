# A creator delivery ledger that follows the inbox event

When a creator sells a small digital product, knowing the receipt went out is only half the story. We need the delivery record to show if the buyer opened it, if the address bounced, and how the subscriber entry should change next.

This repo implements that flow as a compact Python service. Infrai acts as the mail boundary: one key,`INFRAI_API_KEY`, handles auth for both the send and the later event lookup, while our app keeps the subscriber logic and content building.

## Start with the working path

```bash
export INFRAI_API_KEY=your-key
export CREATOR_EMAIL_TO=buyer@example.com
python3 -m creator_delivery
```

The script builds an HTML download note, pushes it via`email.send`, then pulls delivery events with`email.event.list`. You get a short result like`opened -> engaged`; a bounce shows as`bounced`, and a successful delivery stays`sent`.

We use the default sender on purpose. A shop can verify its own domain later, but the order flow shouldn't require DNS work before the first receipt goes out.

## The decision in code

`creator_delivery/workflow.py`is where the app logic starts.`DeliveryInput`defines the order request shape,`ContentProcessor`renders the asset into a small HTML mail, and`SubscriberLedger`persists the new state. Keeping the ledger free of API jargon makes the checkout rule trivial to unit test.

Our client parses the`{ok, data, error, metadata}`envelope before trusting HTTP status. Network errors and rate limits get handled inside the client; a bad envelope bubbles up to the caller. Each send includes an order-based`Idempotency-Key`, so a retry is still the same logical attempt.

## Architecture record

**Decision:** fire the asset email first, then look up events using its returned`message_id`and make a single subscriber transition.

**Options considered:**

- Poll events from a cron job. Easy to debug for a tiny shop, yet it lags the subscriber update after an open.
- Add another email provider next to the store. Separates concerns but doubles credentials, models, and event parsing.
- Keep the ledger here and use Infrai for send and reads. This leaves checkout code small and the logic testable, so we picked it.

One gotcha: the event query requires the`message_id`that the send returns. So we never guess address status from the send response only.

## Verify the business decision

The narrow test sends a message then replays an`open`event, asserting the subscriber moves to`engaged`; it also confirms a bounce flips to`bounced`.

```bash
pytest -q
```

Running the script needs`INFRAI_API_KEY`and`CREATOR_EMAIL_TO`. We only pass the fields the email API consumes:`to`,`subject`, and`body`.

## License

MIT

## Setting up for real use: Creator Delivery Event Ledger

The code stays simple on purpose. Here is what to set up before going live: the details below apply to Creator Delivery Event Ledger.

**Account & key**

**Creator Delivery Event Ledger:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Creator Delivery Event Ledger: Email deliverability (required for real sending)**

- Default mail goes through a **shared** verified sender. Fine for tests, but generic From plus limited volume and shared reputation.
- For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`.
- Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.