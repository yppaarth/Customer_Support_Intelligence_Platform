import time
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.commerce import Customer, Order
from app.models.enums import Role
from app.models.ticket import ApprovalRequest, ToolInvocation
from app.security.auth import Principal


class ToolContext(BaseModel):
    organization_id: str
    ticket_id: str | None = None
    actor_user_id: str
    actor_role: str


class CustomerProfileInput(BaseModel):
    customer_id: str


class OrderInput(BaseModel):
    order_number: str


class RefundApprovalInput(BaseModel):
    order_number: str
    amount: float = Field(gt=0)
    reason: str = Field(min_length=5, max_length=1000)
    idempotency_key: str = Field(min_length=8, max_length=160)


def _record(
    db: Session,
    ctx: ToolContext,
    name: str,
    status_value: str,
    duration_ms: int,
    args: dict,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    db.add(
        ToolInvocation(
            organization_id=ctx.organization_id,
            ticket_id=ctx.ticket_id,
            tool_name=name,
            status=status_value,
            duration_ms=duration_ms,
            input_summary=args,
            result_summary=result or {},
            error=error,
        )
    )


def get_customer_profile(db: Session, ctx: ToolContext, args: CustomerProfileInput) -> dict:
    customer = db.scalar(
        select(Customer).where(
            Customer.id == args.customer_id,
            Customer.organization_id == ctx.organization_id,
        )
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "tier": customer.tier,
        "subscription_status": customer.subscription_status,
    }


def get_order_status(db: Session, ctx: ToolContext, args: OrderInput) -> dict:
    order = db.scalar(
        select(Order).where(Order.order_number == args.order_number, Order.organization_id == ctx.organization_id)
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_number": order.order_number,
        "status": order.status,
        "tracking_number": order.tracking_number,
    }


def get_order_details(db: Session, ctx: ToolContext, args: OrderInput) -> dict:
    order = db.scalar(
        select(Order).where(Order.order_number == args.order_number, Order.organization_id == ctx.organization_id)
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "tracking_number": order.tracking_number,
    }


def get_refund_policy(db: Session, ctx: ToolContext, args: BaseModel | None = None) -> dict:
    return {
        "summary": "Refund requests require policy evidence. High-value or suspicious refunds create approval requests.",
        "requires_approval_over_usd": 100,
    }


def get_subscription_status(db: Session, ctx: ToolContext, args: CustomerProfileInput) -> dict:
    profile = get_customer_profile(db, ctx, args)
    return {"customer_id": profile["id"], "subscription_status": profile["subscription_status"]}


def request_refund_approval(db: Session, ctx: ToolContext, args: RefundApprovalInput) -> dict:
    if ctx.actor_role not in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER, Role.SUPPORT_AGENT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refund approval not allowed")
    existing = db.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == ctx.organization_id,
            ApprovalRequest.request_type == "refund",
            ApprovalRequest.details["idempotency_key"].as_string() == args.idempotency_key,
        )
    )
    if existing:
        return {"approval_request_id": existing.id, "status": existing.status, "idempotent": True}
    approval = ApprovalRequest(
        organization_id=ctx.organization_id,
        ticket_id=ctx.ticket_id or "",
        request_type="refund",
        requested_by_user_id=ctx.actor_user_id,
        details=args.model_dump(),
    )
    db.add(approval)
    db.flush()
    return {"approval_request_id": approval.id, "status": approval.status, "idempotent": False}


TOOL_REGISTRY: dict[str, tuple[type[BaseModel] | None, Callable[..., dict]]] = {
    "get_customer_profile": (CustomerProfileInput, get_customer_profile),
    "get_order_status": (OrderInput, get_order_status),
    "get_order_details": (OrderInput, get_order_details),
    "get_refund_policy": (None, get_refund_policy),
    "get_subscription_status": (CustomerProfileInput, get_subscription_status),
    "request_refund_approval": (RefundApprovalInput, request_refund_approval),
}


def invoke_tool(
    db: Session,
    principal: Principal,
    tool_name: str,
    payload: dict[str, Any],
    ticket_id: str | None = None,
) -> dict:
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail="Tool not registered")
    schema, fn = TOOL_REGISTRY[tool_name]
    args = schema(**payload) if schema else None
    ctx = ToolContext(
        organization_id=principal.organization_id,
        ticket_id=ticket_id,
        actor_user_id=principal.user.id,
        actor_role=principal.role,
    )
    start = time.perf_counter()
    try:
        result = fn(db, ctx, args) if args is not None else fn(db, ctx)
        _record(db, ctx, tool_name, "success", int((time.perf_counter() - start) * 1000), payload, result)
        return result
    except Exception as exc:
        _record(db, ctx, tool_name, "error", int((time.perf_counter() - start) * 1000), payload, error=str(exc))
        raise
