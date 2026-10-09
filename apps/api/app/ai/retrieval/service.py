import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import DocumentChunk, KnowledgeDocument
from app.schemas.ai import RetrievedChunk


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def retrieve_chunks(db: Session, organization_id: str, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    query_tokens = tokenize(query)
    rows = db.execute(
        select(DocumentChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeDocument.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.organization_id == organization_id,
            KnowledgeDocument.organization_id == organization_id,
            KnowledgeDocument.archived.is_(False),
            KnowledgeDocument.status == "active",
        )
    ).all()
    scored: list[tuple[float, DocumentChunk, KnowledgeDocument]] = []
    for chunk, doc in rows:
        overlap = len(query_tokens & tokenize(chunk.content))
        score = overlap / max(1, len(query_tokens))
        if score > 0:
            scored.append((score, chunk, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            title=doc.title,
            section=chunk.section,
            page_number=chunk.page_number,
            content=chunk.content,
            score=score,
        )
        for score, chunk, doc in scored[:top_k]
    ]


def validate_citations(citations: list[RetrievedChunk], evidence: list[RetrievedChunk]) -> list[bool]:
    evidence_ids = {item.chunk_id for item in evidence}
    return [citation.chunk_id in evidence_ids for citation in citations]
