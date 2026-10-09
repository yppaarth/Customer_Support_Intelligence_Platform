# Implementation Plan

## Phase 1: Inspect And Plan

The repository was empty except for `.git`, so ResolveIQ is initialized from scratch. The first vertical slice proves auth, tenant isolation, tickets, knowledge retrieval, AI draft generation, human review, analytics, and evaluation.

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

- Backend: `pytest` passes with 8 tests covering login, ticket processing, webhook idempotency, partial imports, knowledge upload/archive, read-only denial, tenant isolation, and evaluation report generation.
- Evaluation: deterministic synthetic suite generated `evaluation/reports/latest.json` with 105 cases and actual 85.7% classification/escalation accuracy.
- Frontend: `npm run build` passes.
- Production frontend audit: `npm audit --omit=dev` reports 0 vulnerabilities.

## Remaining Hardening

- Replace deterministic token-overlap retrieval with pgvector-backed embeddings in the worker path.
- Add real PDF extraction and object storage handling.
- Expand E2E browser tests and frontend component tests.
- Migrate Vite/Tailwind dev tooling through their breaking major versions to clear full dev audit output.
- Replace FastAPI `on_event` startup hook with lifespan handlers and move datetime defaults to timezone-aware UTC.
