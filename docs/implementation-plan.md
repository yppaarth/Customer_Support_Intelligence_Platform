# Implementation Plan

## Phase 1: Inspect And Plan

The repository was empty except for `.git`, so ResolveIQ is initialized from scratch. The first priority is the narrow product vertical slice: authentication, document ingestion, ticket creation, tenant-scoped retrieval, cited draft generation, and human approval. Dashboards, analytics, evaluation views, and admin surfaces are useful only after this slice works end to end.

## Vertical Slice First

Complete and preserve this golden path before expanding breadth:

1. A seeded user authenticates into a tenant.
2. An admin or manager ingests a knowledge document.
3. An agent creates a customer support ticket.
4. The backend classifies the ticket and retrieves tenant-scoped evidence from the ingested document.
5. The AI pipeline generates a draft with citations that map to retrieved chunks.
6. The frontend shows the draft and exact sources.
7. A human edits and approves the draft.
8. The approved state, audit event, citations, and ticket status are persisted.

The executable backend proof is `test_vertical_slice_auth_doc_ticket_retrieval_cited_draft_and_approval`.

## Phase 2: Foundation

- Backend: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Argon2, JWT, pytest.
- Frontend: React, TypeScript strict mode, Vite, Tailwind, TanStack Query, React Router, Recharts, Hook Form, Zod.
- Infra: Docker Compose with Postgres/pgvector, Redis, API, worker, frontend.
- Verification: backend unit tests and frontend type/build checks.

## Phase 3: Ticket Workflow

Implement manual, CSV/JSON-style normalized ingestion, authenticated webhook ingestion, inbox filters, detail actions, assignment, notes, approval/rejection, resolution, and reopen. Seed 50+ synthetic Northstar tickets across categories and risk levels.

## Phase 4: AI Pipeline

Implement mock/OpenAI provider interface, classification schema validation, deterministic risk policy, retrieval, citation validation, controlled tools, response generation, cost tracking, and persisted escalation decisions.

## Phase 5: Evaluation And Analytics

Create synthetic evaluation cases, run deterministic suite, persist results, expose analytics derived from database records, and clearly distinguish seed/demo/evaluation metrics.

## Phase 6: Hardening

Add tenant isolation, RBAC, idempotency, state transition, tool authorization, provider failure, and citation tests. Add structured logs, request IDs, retry limits, and failed task surfaces.

## Phase 7: Deployment Documentation

Add CI, Dockerfiles, AWS Terraform skeleton, backup/restore notes, secrets guidance, and troubleshooting. Cloud deployment requires explicit operator action.

## Current Verification

- Backend: `pytest` passes with tests covering the vertical slice, login, ticket processing, webhook idempotency, partial imports, knowledge upload/archive, read-only denial, tenant isolation, and evaluation report generation.
- Evaluation: deterministic synthetic suite generated `evaluation/reports/latest.json` with 105 cases and actual 85.7% classification/escalation accuracy.
- Frontend: `npm run build` passes.
- Production frontend audit: `npm audit --omit=dev` reports 0 vulnerabilities.

## Remaining Hardening

- Replace deterministic token-overlap retrieval with pgvector-backed embeddings in the worker path.
- Add real PDF extraction and object storage handling.
- Expand E2E browser tests and frontend component tests.
- Migrate Vite/Tailwind dev tooling through their breaking major versions to clear full dev audit output.
- Replace FastAPI `on_event` startup hook with lifespan handlers and move datetime defaults to timezone-aware UTC.
