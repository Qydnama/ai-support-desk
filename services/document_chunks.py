from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID, uuid5

from models.document_chunks import DocumentChunk
from services.document_text_extraction import (
    ExtractedBlock,
    ExtractedDocument,
)
from settings import settings


@dataclass(frozen=True, slots=True)
class DocumentChunkDraft:
    content: str
    content_hash: str
    page_start: int | None
    page_end: int | None


@dataclass(frozen=True, slots=True)
class _ChunkPart:
    text: str
    page_number: int | None


def build_document_chunks(
    *,
    organization_id: UUID,
    document_id: UUID,
    extracted_document: ExtractedDocument,
) -> list[DocumentChunk]:
    drafts = _build_chunk_drafts(extracted_document)
    index_version = settings.document_chunk_index_version

    return [
        DocumentChunk(
            id=uuid5(
                document_id,
                f"{index_version}:{chunk_index}",
            ),
            organization_id=organization_id,
            document_id=document_id,
            chunk_index=chunk_index,
            content=draft.content,
            content_hash=draft.content_hash,
            page_start=draft.page_start,
            page_end=draft.page_end,
            index_version=index_version,
        )
        for chunk_index, draft in enumerate(drafts)
    ]


def _build_chunk_drafts(
    extracted_document: ExtractedDocument,
) -> list[DocumentChunkDraft]:
    max_chars = settings.document_chunk_max_chars
    overlap_chars = settings.document_chunk_overlap_chars
    parts = _split_blocks_into_parts(
        extracted_document.blocks,
        max_chars=max_chars,
    )

    drafts: list[DocumentChunkDraft] = []
    current_parts: list[_ChunkPart] = []

    for part in parts:
        if current_parts and (
            _parts_length(current_parts) + 2 + len(part.text)
            > max_chars
        ):
            drafts.append(_create_draft(current_parts))

            overlap_limit = min(
                overlap_chars,
                max_chars - len(part.text) - 2,
            )
            current_parts = _take_tail_parts(
                current_parts,
                max_chars=max(overlap_limit, 0),
            )

        current_parts.append(part)

    if current_parts:
        drafts.append(_create_draft(current_parts))

    return drafts


def _split_blocks_into_parts(
    blocks: tuple[ExtractedBlock, ...],
    *,
    max_chars: int,
) -> list[_ChunkPart]:
    parts: list[_ChunkPart] = []

    for block in blocks:
        for text in _split_text(
            block.text,
            max_chars=max_chars,
        ):
            parts.append(
                _ChunkPart(
                    text=text,
                    page_number=block.page_number,
                ),
            )

    return parts


def _split_text(
    text: str,
    *,
    max_chars: int,
) -> list[str]:
    remaining = text.strip()
    parts: list[str] = []

    while len(remaining) > max_chars:
        split_at = remaining.rfind(
            " ",
            0,
            max_chars + 1,
        )

        if split_at <= 0:
            split_at = max_chars

        parts.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    if remaining:
        parts.append(remaining)

    return parts


def _take_tail_parts(
    parts: list[_ChunkPart],
    *,
    max_chars: int,
) -> list[_ChunkPart]:
    if max_chars == 0:
        return []

    selected: list[_ChunkPart] = []
    remaining_chars = max_chars

    for part in reversed(parts):
        separator_size = 2 if selected else 0
        required_chars = len(part.text) + separator_size

        if required_chars <= remaining_chars:
            selected.append(part)
            remaining_chars -= required_chars
            continue

        available_text_chars = (
            remaining_chars - separator_size
        )

        if available_text_chars > 0:
            selected.append(
                _ChunkPart(
                    text=part.text[
                        -available_text_chars:
                    ].lstrip(),
                    page_number=part.page_number,
                ),
            )

        break

    return list(reversed(selected))


def _create_draft(
    parts: list[_ChunkPart],
) -> DocumentChunkDraft:
    content = "\n\n".join(part.text for part in parts)
    page_numbers = [
        part.page_number
        for part in parts
        if part.page_number is not None
    ]

    return DocumentChunkDraft(
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        page_start=min(page_numbers) if page_numbers else None,
        page_end=max(page_numbers) if page_numbers else None,
    )


def _parts_length(
    parts: list[_ChunkPart],
) -> int:
    return sum(len(part.text) for part in parts) + 2 * (
        len(parts) - 1
    )