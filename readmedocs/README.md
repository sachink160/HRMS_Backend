# HRMS Backend API (Production Guide)

This document is intended for production operators and integrators. It summarizes the API surface and operational controls without exposing internal environment details.

## Overview

- Framework: FastAPI (async)
- Database: PostgreSQL (async driver)
- ORM: SQLAlchemy 2.x (async)
- Auth: JWT-based with role RBAC (user, admin, super-admin)
- Core domains: authentication, users, leaves, holidays, tasks, employees, email, admin dashboard

## Base URL & Docs

Configure per environment:
- `API_BASE_URL` – public HTTPS origin for this service
- Interactive docs exposed at `/docs` and `/redoc` when enabled for that environment.

Do not publish internal hostnames. Lock down docs with auth in production if exposed.

## Authentication

- Authorization header: `Bearer <jwt>`
- Tokens are short-lived; refresh tokens managed by the client application.
- Enforce HTTPS and secure cookie/headers at the edge or API gateway.

## Endpoint Families (high level)

- **/auth**: login, register, profile, admin registration (super-admin only)
- **/users**: self profile, admin user listing, status toggles, document uploads
- **/leaves**: apply, list, approve/reject (admin), status updates
- **/holidays**: CRUD for holidays (admin), upcoming list
- **/tasks**: CRUD, filters, summary; soft delete via `is_active`
- **/employees**: employee details and employment history (admin)
- **/admin**: dashboard metrics, user lifecycle actions
- **/email**: SMTP settings, templates, send/test (super-admin)
- **/health**: liveness probe

For full request/response schemas, rely on the generated OpenAPI under `/docs` or `/redoc` in the target environment.

## Data & Validation Notes

- Datetimes must be ISO 8601 with timezone.
- Pagination: `offset`/`limit` (limit capped server-side).
- File uploads: size-limited (10MB) and restricted to safe types; certain documents require approval.
- Leave totals support 0.5 day increments; overlapping or past-dated requests are rejected.

## Error Model

Standard JSON structure:
```json
{ "detail": "message" }
```

Common statuses: 200/201 success, 400 validation, 401 unauthorized, 403 forbidden, 404 not found, 422 validation, 500 server error.

## Operations & Security

- Run behind an API gateway or ingress enforcing TLS, rate limits, and request size caps.
- Configure CORS to the approved origins only.
- Enable structured logging and ship to centralized logging; avoid logging sensitive payloads.
- Metrics/health: use `/health` for liveness; add readiness checks via database reachability if required.
- Secrets: manage via vault/secret manager; never commit credentials or SMTP details.
- Background tasks (email, document processing) should be monitored; configure retries and dead-lettering if using queues.

## Database & Migrations

- Schema managed via Alembic migrations; run migrations during deployment before serving traffic.
- Keep migrations immutable; promote through environments with the same artifact.
- Backups: schedule regular DB backups and test restores.

## Email

- SMTP configuration is environment-scoped and should be stored securely.
- Use the `/email/settings/test-connection` endpoint in non-prod to validate connectivity before enabling sends.
- Templates and logs are restricted to super-admins; ensure RBAC is enforced at the gateway as well.

## Deployment Checklist

- [ ] Set `API_BASE_URL`, database DSN, JWT secrets, SMTP secrets, CORS origins.
- [ ] Run database migrations for the target release.
- [ ] Enable HTTPS termination and rate limiting.
- [ ] Verify `/health` and `/docs` availability (if permitted) post-deploy.
- [ ] Confirm logging/metrics are flowing to the monitoring stack.

## Support

- Confirm upstream dependencies (database, SMTP, object storage) are reachable before raising incidents.
- Capture request IDs in logs to correlate across services.
- Keep client apps in sync with the deployed OpenAPI version.
