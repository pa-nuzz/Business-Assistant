# Design: Stability & UX Hardening (all phases)

Date: 2026-09-23

## Problem summary (root causes)
1. **Cross-origin API** (`localhost:3000` → `localhost:8000`): CORS preflights, Firefox `NS_ERROR_CONNECTION_REFUSE` (localhost→`::1` vs IPv4-only bind), flaky login, refresh→`/login` on reload, task create "needs re-login", excess OPTIONS traffic.
2. **Slow chat first token**: serial pipeline (intent LLM → task-router LLM → serial tool loop → synthesis stream), `_get_context_brief` rebuilt (≈5 DB queries) on *every* LLM call, provider failover stall up to ~65 s.
3. **Bland chat thinking state** (16px logo + 3 dots), no streaming affordance.
4. **Login vs signup are hand-coded differently**; post-login layout offsets; fixed-px components break small screens.
5. **Email to spam** — mostly DNS (SPF/DKIM/DMARC) + From/headers hygiene.

## Phase 1 — Same-origin API proxy
- `frontend/next.config.ts`: add `rewrites()` mapping `/api/v1/:path*` → `${BACKEND_ORIGIN}/api/v1/:path*`. `BACKEND_ORIGIN` = server env, fallback = origin of `NEXT_PUBLIC_API_BASE_URL`, fallback `http://localhost:8000`.
- `frontend/src/lib/api.ts`: `API_BASE = '/api/v1'` (relative). All axios + SSE fetch go same-origin → no CORS/preflights/cookie issues.
- Refactor refresh so the 401 interceptor and `auth.refreshSession` share one deduped `refreshAccessToken()` promise (fixes latent parallel-refresh race).
- SSE `/chat/stream/` through `rewrites()`: verify token-by-token in browser. If Next buffers, replace with a Route Handler proxy for that one path.
- Dev infra: bind backend dual-stack so `localhost:8000` resolves on `::1` too (daphne `-b [::]`), fixing WS + any direct calls in Firefox. Document in README/dev notes.
- Keep existing CORS settings (harmless; WS/direct tools unaffected).

## Phase 2 — Chat speed
- Build the context brief once per turn and pass it into provider calls (`call_model`/`call_model_stream` accept optional `context_brief`), skipping the per-call rebuild.
- Parallelize independent tool calls in `execute_intelligent_plan` (thread pool, results reordered by index); run the two web searches concurrently.
- Cheaper task routing: reuse the intent-classification output to seed the plan; only call the task-router LLM when regex/entity extraction can't determine parameters.
- Emit a `data: {"thinking": ...}` event at the very start of `chat_stream.event_stream` (before orchestration) so the UI shows activity instantly.
- Tighten provider timeouts (Gemini 15→10 s etc.) to cap worst-case failover stall.
- Measure first-token latency before/after via browser timing.

## Phase 3 — Chat UI
- Replace 16px thinking indicator with a deliberate animated component (brand orb + pulse rings + "Aiden is thinking" + dots) sized to feel alive but not dominate.
- Add a streaming caret at the end of an in-flight assistant message.

## Phase 4 — Auth pages + layout/responsive
- One shared `AuthShell` layout component; login and signup render through it (identical left panel, labels, buttons, spacing).
- Fix post-login alignment: consistent page padding across chat/tasks/documents/dashboard; adjust the floating expand button overlap (`left-[84px]`).
- Fluidize fixed widths: notification panels (`w-[360px]/[380px]`), doc preview (`800×1100`), onboarding modal padding — all `max-w-*` + `w-full` where needed.

## Phase 5 — Email deliverability
- `services/email_service.py`: `Reply-To`, `Message-ID`, From aligned with authenticated SMTP user, text+HTML multipart.
- README section: exact SPF/DKIM/DMARC records for the sending domain + note that placement requires those DNS records (honest limit).

## Verification
- P1: browser network log shows zero `OPTIONS`; login → full reload of `/chat` stays logged in; create task without re-login; SSE arrives incrementally.
- P2: first-token latency drop (browser timing logs); `pytest` green.
- P3/P4: Playwright screenshots at 375/768/1280 px.
- P5: send a test email, inspect headers.
- Always: `npm run lint`, `npm run build`, `python -m pytest`.

## Non-goals
- No theme change (light theme stays).
- No WebSocket rewrite for chat (chat is SSE); notifications WS left cross-origin but dual-stack bind fixes Firefox.
- No guaranteed inbox delivery (needs DNS).