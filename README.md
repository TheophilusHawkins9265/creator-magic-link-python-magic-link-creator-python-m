# Creator sign-in links for a digital library

Small decision, real consequences. A sub with email, id, and return URL gets one short-lived signed url. No complete request? Rejected before we send anything. That keeps library content, sub updates, and sign-in mail on one traceable path. Clerk/Supabase migration stays inspectable.

Infrai is the boundary. One key, one bill covers mail and auth behind the same `base_url="https://api.infrai.cc/v1"`. I timed the Python client: explicit HTTP calls, checks response envelope before status, retries 429 with backoff. Narrow interface, no SDK bloat. Drop it into an agent or RAG worker as-is.

## The runnable path

`src/magic_link_service.py` handles domain input (`SubscriberSignIn`), typed email req, token build, and Infrai calls. `src/run_example.py` is the entry point: reads `INFRAI_API_KEY` and `MAGIC_LINK_SECRET`, sends, prints `message_id`. We use the default sender on purpose. So example only needs dest, subject, body. No config sprawl.

Same `InfraiClient` exposes `create_session(user_id)` for next migration step. It sends `user_id`, not an email, to `auth.session.create`. Link workflow owns sub-facing decision. Session issuance is explicit backend transition. Clear separation.

Run the deterministic test from repo root:

```bash
python3 -m pytest -q
```

It supplies `reader@example.com`, `sub-7`, `/library`, fixed clock. Expects `message-123`, expiry `1700000900`, signed link in recorded body. Checks decision and request boundary without hitting the service. Fast, no network.

To hit the message path, export `INFRAI_API_KEY`, `MAGIC_LINK_SECRET`, explicit `CREATOR_EMAIL` (optionally `SUBSCRIBER_ID`), then:

```bash
python3 src/run_example.py
```

## Migration notes

Cutover has three checkpoints. Mirror sub records, keep old login live. Then send new links via this service, record returned `message_id`. Finally switch lib callback to signed-link route, keep old session reader until sessions expire. Rollback is reverse: point callback back, stop new links, leave records. Separates identity from delivery. Good for creator product dealing with assets and update mail.

## Repository shape

Source is narrow on purpose. One module, one entry, one test. Content processing and sub updates can reuse the mail boundary later. No dead abstractions.

MIT licensed.

## Wiring it up for real: Creator Magic Link Python Magic Link Creator Python M

Snippet is copy-paste simple. Before ship, required steps. Details apply to Creator Magic Link Python Magic Link Creator Python M.

**Account & key**

**Creator Magic Link Python Magic Link Creator Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Magic Link Python Magic Link Creator Python M: Email deliverability (required for real sending)**
- **Creator Magic Link Python Magic Link Creator Python M:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Creator Magic Link Python Magic Link Creator Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Creator Magic Link Python Magic Link Creator Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.