# Sentry Production Monitoring & Observability Guide
## (`docs/SENTRY_MONITORING.md`)

This document defines the configuration, security filtering, and quota preservation rules for **Sentry Crash Reporting and Application Performance Monitoring (APM)** in this repository.

---

## 1. Environment Gating & Activation Rules

To prevent flooding Sentry dashboards with development noise and exhausting monthly free quota limits:

- **Local Development (`NODE_ENV=development` / `NODE_ENV=test`)**:
  - Sentry is **strictly disabled** (zero network overhead, zero quota consumption), even if `SENTRY_DSN` contains a value.
- **Production & Staging (`NODE_ENV=production` or `NODE_ENV=staging`)**:
  - Sentry is automatically initialized if and only if `SENTRY_DSN` is populated in `.env`.

```bash
#------------------ MONITORING & OBSERVABILITY ------------------
# Leave empty or keep NODE_ENV=development to keep Sentry OFF.
# Set NODE_ENV=production and provide valid DSN to activate Sentry.
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

---

## 2. The 7 Production Guardrails Implemented

The setup in [src/util/monitoring.py](file:///c:/Users/Sourav/Documents/Start/src/util/monitoring.py) strictly enforces the 7 enterprise best practices:

| # | Guardrail / Rule | Implementation Mechanism | Purpose |
| :--- | :--- | :--- | :--- |
| **1** | **PII & Credential Scrubbing** | `scrub_sensitive_data()` with `send_default_pii=False` | Filters `password`, `otp`, `token`, `secret`, `credit_card`, and `authorization` headers to `[FILTERED]`. |
| **2** | **Strict Environment Switch** | `init_sentry()` | Ensures Sentry only fires in `production` or `staging`. |
| **3** | **Quota Preservation (10% Sampling)** | `traces_sample_rate=0.1`, `profiles_sample_rate=0.1` | Samples 10% of requests for performance tracing rather than 100%, preserving server CPU and monthly limits. |
| **4** | **Noise Reduction (Drop 4xx Client Errors)** | `scrub_sensitive_data()` | Automatically drops `ApiError` with status 400, 401, 404, 422. Only real **5xx server crashes** trigger alerts. |
| **5** | **Filter Health Checks** | `filter_transactions()` | Drops `/health`, `/health/live`, `/health/ready`, `/metrics`, and `/docs` from transaction tracing. |
| **6** | **User Impact Tracking** | `set_sentry_user()` in [src/app/middleware/auth.py](file:///c:/Users/Sourav/Documents/Start/src/app/middleware/auth.py) | Attaches verified `userId`, `role`, and `email` to error scopes for instant impact analysis. |
| **7** | **Auto-Instrumented Integrations** | FastAPI, Starlette, Redis, and PyMongo | Provides full waterfall tracing across HTTP routes, Redis cache hits, and MongoDB queries. |

---

## 3. How to Test Sentry in Staging/Production

1. Set `NODE_ENV=production` in `.env`.
2. Set `SENTRY_DSN=https://your-key@o0.ingest.sentry.io/your-project-id`.
3. To test a crash, add a temporary debug endpoint or test script:
   ```python
   @app.get("/sentry-debug")
   async def trigger_error():
       return 1 / 0
   ```
4. Check your Sentry project dashboard — the `ZeroDivisionError` report with full stacktrace, sanitized headers, and user context appears within seconds!
