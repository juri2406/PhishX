# Person 2 next-stage implementation — 21 October 2026

> Update, 21 October 2026: the opt-in research CNN/cascade provider and minimal
> route metadata integration are now supplied. It failed the broader-source
> false-positive promotion check and remains disabled by default. See
> [Person 1 neural handoff](person1-neural-handoff.md). The original completion
> gates below record the status before that handoff; browser and deployment
> validation remain open.

The classical milestone remains the accepted baseline. This change adds opt-in
live observations, a local launcher, and container deployment configuration.
It does not claim that the final project or deployment is complete.

## Implemented

- `POST /signals` accepts the same URL envelope as `/scan`. Uses Person 1's
  shared `phishx.urls.normalize_url`, never a replacement training parser.
- DNS answers, HTTPS certificate-chain/hostname verification, up to three HEAD
  redirect transitions, and registration age from RDAP. Each observation has an
  explicit available/unavailable/blocked/not_applicable status.
- No submitted page body is read. RDAP JSON only is read, limited to 256 KiB.
  HTTP(S) ports 80/443 only, no credentials. Every hop resolves again and every
  answer must be public. Connections pin one validated IP with original-host SNI
  and Host; no second DNS lookup or environment proxy. IPv6 transition/mapped
  addresses are blocked. Headers limited to 64 KiB; DNS 2 seconds, each probe
  4 seconds, total endpoint 12 seconds. Four concurrent live requests per worker;
  overload returns 429. Timeout returns 504 without altering the text result.
- Explicit server opt-in `PHISHX_LIVE_SIGNALS=1`; fixture mode cannot run live
  checks. User separately clicks **Run live checks** after a model scan.
- React control presents loading, retry and per-signal status. Live observations
  stay separate from classical features and SHAP, and cannot change the score.
- `bash scripts/start-dev.sh --live` starts backend/frontend together on macOS.
  Omit `--live` for text-only operation. Ctrl+C stops children. Occupied ports
  produce actionable guidance without killing existing services.
- Docker/Compose and nginx configurations: localhost-only web port, internal
  backend, read-only model mount, non-root images, same-origin API proxy,
  request size/rate limits. Deployment instructions below.

## Measured verification

- Full Python suite: **72 passed, 11 subtests passed**. Network-policy tests
  inject transports and are not presented as real-world detection evidence.
- Frontend production build passed.
- Real local HTTP smoke with the v6 provider: example.com live DNS, TLS,
  redirects and RDAP returned available. Model score was 26 both before and
  after live checks, with identical probability 0.25875196244571097.
  Exact response: [http-smoke.json](evidence/person2-live/http-smoke.json).
- New UI browser/visual acceptance has **not** been performed in this session.
  Existing milestone screenshots predate this feature and are not new evidence.
- Docker is unavailable on this Mac. Container builds and Compose smoke tests
  have **not** run. Deployment is configuration prepared, not deployment verified.

## Completion gates still open

1. Person 1 must provide and evaluate a real CNN/cascade provider and freeze its
   contract. The API still truthfully reports classical/not_implemented. Person 2
   then integrates routing, explanations and model identity with provider tests;
   no fabricated neural result or neural SHAP is supplied.
2. Run desktop/mobile browser acceptance for the new live-check interface:
   disabled mode, successful example.com, private target blocked, unavailable
   TLS/registry, slow backend and retry; preserve keyboard access and result.
3. Build and smoke-test Compose on a Docker host, select hosting and configure
   HTTPS/access control/outbound firewall before making it publicly accessible.
4. Person 3 supplies independent final regression fixtures and human team review.

## Limits of the new signals

RDAP may omit dates, return 404/rate limits, or be unsupported for a suffix.
Private-PSL hosting domains may have no separate registration record. Failure is
unavailable, never zero age. The shared parser's domain grouping remains intact.
HEAD redirects may differ from browser GET behavior. Only the initial URL's TLS
status is displayed; later-hop errors make the redirect check incomplete. DNS is
reported conservatively as unavailable if its subsequent connection fails.
Observations are point-in-time and not a safety certificate. These signals were
not used to train v6; retraining/quality claims belong to Person 1.

## Run locally

```bash
cd /Users/gauri/Documents/ChatGPT/PhishX
bash scripts/start-dev.sh --live
```

Open http://127.0.0.1:5173, scan a URL, then choose **Run live checks**.


## Person 3 browser review update

The new default/live-check and opt-in research interfaces have now received a
focused desktop/mobile browser pass and independent fixture review. See
[Person 3 final-stage review](person3-final-review.md). Model regressions, the
unavailable-signal scope copy, result-focus follow-up and Docker/hosting remain
open. The earlier "not performed" statements above describe the original
Person 2 session, not the current evidence.
