from itertools import cycle

from sqlalchemy import select

import app.models  # noqa: F401
from app.db.session import Base, SessionLocal, engine
from app.models.commerce import Customer, Order
from app.models.enums import IngestionSource, Role
from app.models.knowledge import DocumentChunk, DocumentVersion, KnowledgeDocument
from app.models.organization import Organization, OrganizationMembership, OrganizationSettings, User
from app.schemas.tickets import TicketCreate
from app.security.auth import Principal, hash_password
from app.services.tickets import create_ticket, process_ticket

PASSWORD = "ResolveIQDemo!23"

POLICIES = [
    (
        "Refund Policy v3",
        "Refunds",
        "Customers may request a refund within 30 days of delivery for unused items. Damaged items can be refunded or replaced after photo verification. Refunds above 100 USD require manager approval.",
    ),
    (
        "Shipping And Delivery Policy",
        "Shipping",
        "Standard delivery takes 5 to 7 business days. Delayed orders should be checked against carrier tracking. If tracking has no movement for 5 business days, agents may offer a replacement shipment.",
    ),
    (
        "Subscription Cancellation Guide",
        "Subscriptions",
        "Customers can cancel monthly subscriptions before the next billing date. Agents may explain cancellation steps but must not promise refunds for already shipped subscription boxes without policy review.",
    ),
    (
        "Account Security Playbook",
        "Security",
        "Account takeover, suspicious login, payment fraud, and requests for sensitive personal information must be escalated to a manager. Agents should never ask for full card numbers or passwords.",
    ),
    (
        "Billing Dispute Procedure",
        "Billing",
        "Duplicate charges should be verified against order and payment records. High-impact billing disputes and chargeback threats require human review before any customer-facing commitment.",
    ),
    (
        "Unsupported Request Policy",
        "Unsupported",
        "If the customer asks for actions outside Northstar Commerce policies or the evidence is insufficient, the AI draft must recommend escalation instead of inventing an answer.",
    ),
]

SUBJECTS = [
    ("Refund request for unopened item", "I want a refund for an unused item delivered last week."),
    ("Delayed order has no tracking movement", "My order is delayed and tracking has not moved for six days."),
    ("Product arrived damaged", "The lamp arrived damaged and I have photos. I need a replacement."),
    ("Cancel subscription", "Please cancel my monthly subscription before the next billing date."),
    ("Billing discrepancy", "I was double charged and this is unacceptable."),
    ("Account access problem", "I cannot access my account after a suspicious login."),
    ("Technical troubleshooting", "The checkout page fails when I apply my promo code."),
    ("Frustrated complaint", "I am furious about the lack of updates on my package."),
    ("Ambiguous question", "Can you help me with my thing from last month?"),
    ("Unsupported request", "Can you change another customer's delivery address for me?"),
    ("Potential fraud concern", "This looks like fraud and my card may be stolen."),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(select(Organization).where(Organization.slug == "northstar"))
        if existing:
            print("Seed data already exists")
            return
        org = Organization(name="Northstar Commerce", slug="northstar")
        db.add(org)
        db.flush()
        db.add(OrganizationSettings(organization_id=org.id, autonomous_send_enabled=False))
        users = [
            ("admin@northstar.demo", "Avery Admin", Role.ORG_ADMIN),
            ("manager@northstar.demo", "Morgan Manager", Role.SUPPORT_MANAGER),
            ("agent@northstar.demo", "Sam Agent", Role.SUPPORT_AGENT),
            ("analyst@northstar.demo", "Riley Analyst", Role.READ_ONLY_ANALYST),
        ]
        user_objs: list[User] = []
        for email, name, role in users:
            user = User(email=email, full_name=name, password_hash=hash_password(PASSWORD))
            db.add(user)
            db.flush()
            db.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role=role.value))
            user_objs.append(user)
        customers: list[Customer] = []
        for i in range(1, 31):
            customer = Customer(
                organization_id=org.id,
                name=f"Customer {i:02d}",
                email=f"customer{i:02d}@example.test",
                tier="enterprise" if i % 10 == 0 else "standard",
                subscription_status="active" if i % 7 else "paused",
            )
            db.add(customer)
            db.flush()
            db.add(
                Order(
                    organization_id=org.id,
                    customer_id=customer.id,
                    order_number=f"NS-{1000+i}",
                    status=["processing", "shipped", "delayed", "delivered", "returned"][i % 5],
                    total_amount=39 + i * 3,
                    tracking_number=f"TRK{i:06d}",
                    metadata_json={"synthetic": True},
                )
            )
            customers.append(customer)
        for title, section, content in POLICIES:
            doc = KnowledgeDocument(organization_id=org.id, title=title, source_type="markdown", status="active")
            db.add(doc)
            db.flush()
            version = DocumentVersion(organization_id=org.id, document_id=doc.id, version=1, checksum=title, ingestion_status="complete")
            db.add(version)
            db.flush()
            db.add(
                DocumentChunk(
                    organization_id=org.id,
                    document_id=doc.id,
                    version_id=version.id,
                    chunk_index=0,
                    section=section,
                    page_number=1,
                    content=content,
                    token_count=len(content.split()),
                    metadata_json={"seed": True},
                )
            )
        principal = Principal(user_objs[0], org.id, Role.ORG_ADMIN.value)
        subject_cycle = cycle(SUBJECTS)
        customer_cycle = cycle(customers)
        for i in range(55):
            subject, body = next(subject_cycle)
            customer = next(customer_cycle)
            payload = TicketCreate(
                subject=f"{subject} #{i+1}",
                customer_email=customer.email,
                customer_name=customer.name,
                message=body,
                external_id=f"seed-{i+1}",
                source=IngestionSource.SEED,
            )
            ticket = create_ticket(db, principal, payload)
            process_ticket(db, principal, ticket)
        db.commit()
        print("Seeded ResolveIQ demo data")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
