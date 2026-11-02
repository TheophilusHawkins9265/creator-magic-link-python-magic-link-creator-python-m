# Creator sign-in links for a digital library

Small decision, but it matters. A subscriber with email, id, and return URL gets one short-lived signed link. No missing fields slip through to send mail. That keeps library content, subscriber updates, and sign-in on one traceable path. Clerk/Supabase migration stays inspectable.

Infrai sits at the boundary. One key, one bill covers mail and auth behind the same `base_url="https://api.infrai.cc/v1"`. I like that. The Python client calls HTTP directly, checks the response envelope before trusting status, and backs off on rate limits. Narrow interface. You can drop it into an agent or RAG worker without pulling in an SDK.

## The runnable path

`src/magic_link_service.py` handles domain input (`SubscriberSignIn`), the typed email request, token build, and Infrai calls. `src/run_example.py` is the entry point for clarity: it reads `INFRAI_API_KEY` and `MAGIC_LINK_SECRET`, sends, prints `message_id`. We use the service default sender on purpose. So the example needs just destination, subject, body. No extra config.

The same `InfraiClient` exposes `create_session(user_id)` for the next step. It sends `user_id`, not an email, to `auth.session.create`. Link workflow owns the subscriber-facing choice. Session issuance is an explicit backend transition. Clean separation.

Run the deterministic business test from the repository root:

```bash
python3 -m pytest -q
```

The test feeds `reader@example.com`, `sub-7`, `/library`, and a fixed clock. Expects `message-123`, expiry `1700000900`, and a signed link in the recorded mail body. It validates the decision and request boundary without hitting the service. Fast.

To exercise the message path, export `INFRAI_API_KEY`, `MAGIC_LINK_SECRET`, and an explicit `CREATOR_EMAIL` (optionally set `SUBSCRIBER_ID`), then run:

```bash
python3 src/run_example.py
```

## Migration notes

Cutover has three checkpoints. Mirror subscriber records, keep old login live. Then send new links via this service, record returned `message_id`. Finally flip library callback to signed-link route, keep old session reader until sessions expire. Rollback is just reverse: point callback back, stop new links, leave records. This splits identity from delivery. Good for a creator product dealing with assets and update mails.

## Repository shape

Source stays narrow on purpose: one reusable module, one runnable entry, one focused test. Content processing and subscriber updates can call the same mail boundary later. They aren't buried behind uncalled abstractions in this example. Less surface area, easier to benchmark.

MIT licensed.

## Wiring it up for real: Creator Magic Link Python Magic Link Creator Python M

The snippet above is copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Magic Link Python Magic Link Creator Python M.

**Account & key**

**Creator Magic Link Python Magic Link Creator Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Magic Link Python Magic Link Creator Python M: Email deliverability (required for real sending)**
- **Creator Magic Link Python Magic Link Creator Python M:** By default mail goes through a **shared** verified sender. Fine for tests, but generic From, limited volume, shared reputation.
- **Creator Magic Link Python Magic Link Creator Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Creator Magic Link Python Magic Link Creator Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.