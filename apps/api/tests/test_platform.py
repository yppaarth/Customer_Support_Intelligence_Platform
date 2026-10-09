from fastapi.testclient import TestClient

from app.ai.evaluation.runner import run


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


def test_evaluation_runner_writes_actual_report(tmp_path) -> None:
    output = tmp_path / "report.json"
    report = run(tmp_path / "missing.json", output)
    assert output.exists()
    assert report["total_cases"] == 105
    assert "classification_accuracy" in report
