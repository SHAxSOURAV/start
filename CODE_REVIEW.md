# Code Review — Findings

**Score: 64 / 100** as a reusable client-project template, weighted toward architecture and security.

A "solid skeleton, don't ship it as-is" score. The layering is genuinely good — better than most
starters. The problem is that a template multiplies whatever is in it, and this one currently
multiplies a systematic authorization flaw and a total absence of tests into every project cloned
from it.

| Category                | Score | Why                                                        |
| ----------------------- | ----- | ---------------------------------------------------------- |
| Architecture & layering | 78    | Consistent, predictable, extends cleanly                   |
| Security & auth         | 48    | Auth _gate_ is solid; per-resource authorization is absent |
| Correctness             | 62    | Sound main paths, several real latent bugs                 |
| Maintainability / DX    | 60    | Duplication, dead code, import-time side effects           |
| Python / FastAPI idiom  | 55    | Deliberately fights the framework                          |
| Testability             | 25    | No harness at all                                          |

Scope: code quality and architecture only — CI, Docker and deployment were explicitly excluded.

---

## What's actually good

Not padding — these are the reasons it isn't in the 40s.

- **The module shape is rigorously consistent.** All 8 modules are model / controller / service /
  routes with no exceptions. A new module drops in without a judgment call, and the scaffolder
  emits all four files correctly. This is the single best thing about the codebase.
- **Cross-cutting concerns are centralised properly** — one error-translation layer, one response
  envelope, one query builder, config validated at boot with a clear failure message.
- **The auth gate itself is well built**: bearer parsing, verification, blocked/inactive checks,
  role gate, and a working optional-auth path.
- **Genuine security wins**: bcrypt with configurable rounds, OTP attempt caps _and_ expiry, regex
  metacharacter escaping in search, NoSQL operator stripping in `filter()`, upload extension derived
  from validated MIME rather than the filename, size/count caps, and upload rollback on request
  failure. The password never appears in a populated `authId`.

---

## The findings that move the score

### 1. Missing ownership checks across four modules — the biggest issue

Every one of these functions **accepts `user_data` and never reads it**:

| Function                                  | Consequence                                                     |
| ----------------------------------------- | --------------------------------------------------------------- |
| `get_feedback`, `delete_feedback`         | Any logged-in user reads or deletes **anyone's** feedback by id |
| `update_review`, `delete_review`          | Any user edits or deletes **anyone's** review                   |
| `get_notification`, `delete_notification` | Any user reads or deletes **anyone's** notification             |
| `get_chat_messages`                       | Any user reads **any** private conversation by chatId           |

[feedback_service.py:63](src/app/module/feedback/feedback_service.py#L63),
[:141](src/app/module/feedback/feedback_service.py#L141),
[review_service.py:81](src/app/module/review/review_service.py#L81),
[:104](src/app/module/review/review_service.py#L104),
[notification_service.py:31](src/app/module/notification/notification_service.py#L31),
[:105](src/app/module/notification/notification_service.py#L105),
[chat_service.py:73](src/app/module/chat/chat_service.py#L73)

The parameter's presence makes it _look_ like the check exists. The fix is small — put the owner in
the filter:

```python
feedback = await Feedback.get_pymongo_collection().find_one(
    {
        "_id": ObjectId(str(query["feedbackId"])),
        "user": ObjectId(str(user_data["userId"])),
    }
)
```

Inherited from the TypeScript original, not introduced by the port. But in a template it is the flaw
that costs most, because it ships to every client.

### 2. SUPER_ADMIN isn't treated as an admin

`user_data["role"] == EnumUserRole.ADMIN` in the feedback, review and notification services sends a
SUPER*ADMIN down the \_normal user* branch — so the highest-privilege account sees less than an admin.
It also contradicts `config.auth_level.admin`, which correctly includes both.
[auth_service.py:159](src/app/module/auth/auth_service.py#L159) gets it right; compare against it.

Current occurrences: [feedback_service.py:94](src/app/module/feedback/feedback_service.py#L94),
[review_service.py:46](src/app/module/review/review_service.py#L46),
[notification_service.py:24](src/app/module/notification/notification_service.py#L24),
[:45](src/app/module/notification/notification_service.py#L45),
[:79](src/app/module/notification/notification_service.py#L79),
[:105](src/app/module/notification/notification_service.py#L105). Inherited.

### 3. Rate limiter — two bugs

[limiter.py:27](src/app/middleware/limiter.py#L27)

```python
limiter_id = id(object())  # object is garbage-collected immediately
```

CPython reuses freed ids, so two limiters can collide and share one bucket. Use
`next(itertools.count())` or `uuid4()`.

And `_windows` ([limiter.py:11](src/app/middleware/limiter.py#L11)) **never evicts** — one entry per
(limiter, IP) forever, a slow memory leak that any scanner accelerates. Needs periodic sweeping of
expired windows.

Introduced by the port.

### 4. Password hashing only fires on insert

[auth_model.py:61](src/app/module/auth/auth_model.py#L61) is `@before_event(Insert)`. Mongoose's
`pre("save")` ran on _every_ save. So:

```python
auth.password = "plaintext"
await auth.save()  # stored in the clear
```

Fix is one line — `@before_event(Insert, Replace, Save)`. The existing `is_hashed()` guard already
prevents double-hashing.

Introduced by the port.

### 5. Error responses echo internal exception text

[global_error_handler.py:163](src/app/middleware/global_error_handler.py#L163) and
[:176](src/app/middleware/global_error_handler.py#L176) send `str(error)` to the client for Mongo and
unhandled errors — which can carry collection names, query shapes and driver internals. Return a
fixed message for 5xx and log the detail instead. Inherited.

### 6. The port fights FastAPI — the main architectural criticism

Every endpoint is `(request: Request) -> JSONResponse` with manual body and query extraction. That
was the right call for a faithful port, but as a _Python_ template the cost is real:

- No response models, so **no generated OpenAPI** (`docs_url=None`) — `docs/openapi.yaml` is
  hand-maintained and _will_ drift
- **40 of 49 endpoints have no schema validation at all** — only the 9 auth routes use
  `validate_request`; everything else relies on runtime `validate_fields` dict checks
- No editor or type assistance at the request boundary

FastAPI was chosen and then its best feature turned off. For a template to be extended for years,
migrate at least request/response models per module.

### 7. Zero tests

The highest-leverage gap for a template specifically. Every project cloned from this starts with no
harness, so nobody adds one. Even four tests plus a working fixture would change the trajectory.

### 8. Smaller but real

- **Triplicated helpers** — `_oid` in [user_service.py:107](src/app/module/user/user_service.py#L107)
  and [admin_service.py:144](src/app/module/admin/admin_service.py#L144), `_object_id` in
  [chat_socket_controller.py:66](src/socket/chat_socket_controller.py#L66); `populate_auth`
  copy-pasted between the user and admin services. Three places to fix one bug.
- **Manual `updatedAt`** — the base document covers insert/replace/save, but every raw `update_one`
  must remember `"updatedAt": utcnow()`. New modules will forget.
- **Import-time side effects** — `config/__init__.py` calls `sys.exit(1)`; `logger.py` creates
  directories on import. Importing anything needs a valid environment.
- **Dead code** — `convert_to_array`, `date_time_validator`, `stripe_currency_validator`,
  `process_file_updates` have **zero** references, plus unused `ApiResponse` / `socket_types`
  TypedDicts and `is_db_up()`.
- **QueryBuilder projection footgun** — `?fields=password` projects any field by name. Harmless on
  today's models; dangerous the day someone runs it over `Auth`. Add a per-model allowlist.

---

## Attribution

**Inherited from the TypeScript original by design** (an exact port was requested, so these were
reproduced): findings 1, 2, 5, and the no-schema-validation half of 6. The port neither fixed nor
worsened them.

**Introduced by the port**: findings 3 and 4. The limiter was hand-written because slowapi couldn't
reproduce the required 429 body, and the identity and eviction were both wrong. The hash hook is a
mistranslation of Mongoose semantics. Both are small fixes and should be treated as bugs rather than
design decisions.

---

## Getting to 85

In rough order of return:

1. Add ownership filters to the seven functions in finding 1 — a couple of hours, and it's the
   difference between a template that leaks data and one that doesn't
2. Fix the limiter and the hash hook (~20 minutes)
3. Replace `role == ADMIN` with `role in config.auth_level.admin` everywhere
4. Add a pytest harness plus three or four tests against `TEST_MONGO_URL`
5. Introduce Pydantic request/response models module by module and switch OpenAPI back on
6. Delete the dead utils; hoist `_oid` and `populate_auth` into `util/`

Steps 1–3 alone move this to roughly 75. Adding 4 and 5 reaches the mid-80s, at which point it's a
template worth cloning.

---

## Provenance

Findings produced in a session run from `../server-setup-template-updated`, but every file reference
resolved to **this** repository (`server-setup-template-python`) — this is the reviewed codebase.

All line references above were re-verified against the current working tree at the time this file was
written; findings 1–5 and 8 are all still present. Nothing here has been fixed yet.

Not covered by this review: CI, Docker, deployment.
