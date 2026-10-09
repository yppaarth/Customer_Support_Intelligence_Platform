# ResolveIQ Architecture

ResolveIQ is a modular monolith. The frontend talks only to the FastAPI API. The API owns authentication, tenant isolation, persistence, orchestration, audit logging, and policy checks. Celery workers run expensive or retryable jobs such as document ingestion, embeddings, ticket processing, and evaluations.

## Boundaries

- `api/v1`: HTTP contracts and route-level authorization.
- `services`: business workflows and transaction boundaries.
- `ai/providers`: model provider abstraction and mock/OpenAI adapters.
- `ai/retrieval`: document chunking, embedding interface, retrieval filters, and citation validation.
- `ai/tools`: typed local commerce tools. Model output may request tools, but the backend independently authorizes and validates them.
- `security`: password hashing, JWT, role checks, CSRF-friendly cookie strategy hooks.
- `observability`: correlation IDs, structured logs, latency metrics, redaction.

## Tenant Isolation

Every tenant-owned table has `organization_id`. Routes derive the active organization from authenticated membership rather than trusting client supplied tenant IDs. Repository helpers require organization scope and tests cover denied cross-tenant reads.

## Transaction Boundaries

- Ticket creation stores the normalized ticket, first message, ingestion record, audit log, and processing status in one transaction.
- Draft generation stores model usage, retrieval evidence, draft, citations, quality result, and optional escalation in one transaction.
- Approval stores the edited final response, status transition, audit log, and any approval request updates in one transaction.

## AI Pipeline

1. Normalize incoming ticket content.
2. Run deterministic risk rules.
3. Call classification provider or fallback classifier.
4. Retrieve tenant-scoped active document chunks.
5. Invoke permissioned tools only when requested and authorized.
6. Generate a grounded draft with citations.
7. Validate citations against retrieved chunks.
8. Evaluate evidence coverage, risk, and confidence.
9. Persist draft or create escalation for human review.

## Security Notes

- Argon2id hashes are used for passwords.
- JWT access tokens are short-lived. Refresh/session storage is modeled for a secure cookie strategy.
- Demo login is disallowed when `ENVIRONMENT=production`.
- Sensitive logs redact passwords, tokens, API keys, and raw conversations.
- Uploads are constrained by extension, MIME type, and size before ingestion.

