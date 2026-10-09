from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.ai.evaluation.runner import run
from app.models.enums import Role
from app.models.organization import Organization, OrganizationMembership, User
from app.security.auth import hash_password


def test_login_and_list_tickets(client: TestClient, token: str) -> None:
    res = client.get("/api/v1/tickets", headers={"authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 50
    assert body["items"]


def test_create_ticket_processes_draft(client: TestClient, token: str) -> None:
    res = client.post(
        "/api/v1/tickets",
        headers={"authorization": f"Bearer {token}"},
        json={
            "subject": "Refund request",
            "customer_email": "case@example.test",
            "customer_name": "Case Customer",
            "message": "I want a refund for an unused item delivered yesterday.",
        },
    )
    assert res.status_code == 201, res.text
    ticket_id = res.json()["id"]
    detail = client.get(f"/api/v1/tickets/{ticket_id}", headers={"authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    assert detail.json()["latest_draft"]["citations"]


def test_vertical_slice_auth_doc_ticket_retrieval_cited_draft_and_approval(
    client: TestClient, token: str
) -> None:
    document = client.post(
        "/api/v1/knowledge",
        headers={"authorization": f"Bearer {token}"},
        json={
            "title": "Loyalty Credit Policy",
            "content": (
                "When a customer reports a sparklepack shipping delay, support agents may offer "
                "a 15 USD loyalty credit after verifying the delayed order. This policy requires "
                "human approval before the response is sent."
            ),
            "source_type": "markdown",
        },
    )
    assert document.status_code == 201, document.text

    created = client.post(
        "/api/v1/tickets",
        headers={"authorization": f"Bearer {token}"},
        json={
            "subject": "Sparklepack shipping delay",
            "customer_email": "vertical.slice@example.test",
            "customer_name": "Vertical Slice",
            "message": "My sparklepack shipping delay has been going on for days. Can you help?",
        },
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]

    detail = client.get(f"/api/v1/tickets/{ticket_id}", headers={"authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    body = detail.json()
    assert body["latest_draft"]["body"]
    citation_titles = {citation["title"] for citation in body["latest_draft"]["citations"]}
    assert "Loyalty Credit Policy" in citation_titles
    assert body["status"] in {"waiting_for_human_review", "approved"}

    approved = client.post(
        f"/api/v1/tickets/{ticket_id}/approve",
        headers={"authorization": f"Bearer {token}"},
        json={"draft_body": body["latest_draft"]["body"] + "\n\nApproved by agent."},
    )
    assert approved.status_code == 200, approved.text

    final = client.get(f"/api/v1/tickets/{ticket_id}", headers={"authorization": f"Bearer {token}"})
    assert final.json()["status"] == "approved"
    assert final.json()["latest_draft"]["status"] == "approved"


def test_webhook_idempotency(client: TestClient, token: str) -> None:
    payload = {
        "subject": "Delayed order",
        "customer_email": "idem@example.test",
        "message": "My order is delayed and tracking has not moved.",
        "idempotency_key": "idem-123456",
    }
    first = client.post("/api/v1/tickets/webhook", headers={"authorization": f"Bearer {token}"}, json=payload)
    second = client.post("/api/v1/tickets/webhook", headers={"authorization": f"Bearer {token}"}, json=payload)
    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]


def test_import_allows_partial_failures(client: TestClient, token: str) -> None:
    res = client.post(
        "/api/v1/tickets/import",
        headers={"authorization": f"Bearer {token}"},
        json=[
            {
                "subject": "Valid imported refund",
                "customer_email": "import@example.test",
                "message": "I want a refund for an unused item.",
            },
            {"subject": "bad"},
        ],
    )
    assert res.status_code == 207, res.text
    body = res.json()
    assert len(body["created"]) == 1
    assert len(body["failed"]) == 1


def test_knowledge_upload_and_archive(client: TestClient, token: str) -> None:
    upload = client.post(
        "/api/v1/knowledge/upload",
        headers={"authorization": f"Bearer {token}"},
        data={"title": "Warranty policy"},
        files={"file": ("warranty.md", b"Warranty claims require an order number and must be reviewed within 90 days.", "text/markdown")},
    )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["id"]
    archive = client.post(f"/api/v1/knowledge/{doc_id}/archive", headers={"authorization": f"Bearer {token}"})
    assert archive.status_code == 200


def test_read_only_user_cannot_create_ticket(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@northstar.demo", "password": "ResolveIQDemo!23", "organization_slug": "northstar"},
    )
    token = login.json()["access_token"]
    res = client.post(
        "/api/v1/tickets",
        headers={"authorization": f"Bearer {token}"},
        json={
            "subject": "Denied create",
            "customer_email": "deny@example.test",
            "message": "This should not be allowed.",
        },
    )
    assert res.status_code == 403


def test_tenant_isolation_blocks_cross_org_ticket(client: TestClient, token: str) -> None:
    created = client.post(
        "/api/v1/tickets",
        headers={"authorization": f"Bearer {token}"},
        json={
            "subject": "Tenant scoped ticket",
            "customer_email": "tenant@example.test",
            "message": "I want a refund for an unused item.",
        },
    )
    ticket_id = created.json()["id"]
    db = SessionLocal()
    try:
        org = Organization(name="Southstar Commerce", slug="southstar")
        db.add(org)
        user = User(email="admin@southstar.demo", full_name="South Admin", password_hash=hash_password("ResolveIQDemo!23"))
        db.add(user)
        db.flush()
        db.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role=Role.ORG_ADMIN.value))
        db.commit()
    finally:
        db.close()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@southstar.demo", "password": "ResolveIQDemo!23", "organization_slug": "southstar"},
    )
    south_token = login.json()["access_token"]
    denied = client.get(f"/api/v1/tickets/{ticket_id}", headers={"authorization": f"Bearer {south_token}"})
    assert denied.status_code == 404


def test_evaluation_runner_writes_actual_report(tmp_path) -> None:
    output = tmp_path / "report.json"
    report = run(tmp_path / "missing.json", output)
    assert output.exists()
    assert report["total_cases"] == 105
    assert "classification_accuracy" in report
