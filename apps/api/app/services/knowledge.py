import hashlib
import re

from sqlalchemy.orm import Session

from app.models.knowledge import DocumentChunk, DocumentVersion, KnowledgeDocument

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/html",
    "application/octet-stream",
}


def safe_extract_text(filename: str, content_type: str | None, raw: bytes, max_bytes: int) -> str:
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension")
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported MIME type")
    if len(raw) > max_bytes:
        raise ValueError("File is too large")
    text = raw.decode("utf-8", errors="replace")
    if suffix in {".html", ".htm"}:
        text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 20:
        raise ValueError("Document text is too short")
    return text


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += max(1, chunk_size - overlap)
    return chunks


def ingest_document(
    db: Session,
    organization_id: str,
    title: str,
    source_type: str,
    text: str,
) -> KnowledgeDocument:
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    doc = KnowledgeDocument(organization_id=organization_id, title=title, source_type=source_type, status="active")
    db.add(doc)
    db.flush()
    version = DocumentVersion(
        organization_id=organization_id,
        document_id=doc.id,
        version=1,
        checksum=checksum,
        ingestion_status="complete",
    )
    db.add(version)
    db.flush()
    for idx, chunk in enumerate(chunk_text(text)):
        db.add(
            DocumentChunk(
                organization_id=organization_id,
                document_id=doc.id,
                version_id=version.id,
                chunk_index=idx,
                section=title,
                page_number=None,
                content=chunk,
                token_count=len(chunk.split()),
                metadata_json={"ingested": True},
            )
        )
    return doc
