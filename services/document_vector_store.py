from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import (
    ResponseHandlingException,
    UnexpectedResponse,
)

from models.document_chunks import DocumentChunk
from settings import settings

Result = TypeVar("Result")


class DocumentVectorStoreUnavailableError(OSError):
    pass


@dataclass(frozen=True, slots=True)
class DocumentVectorSearchResult:
    chunk_id: UUID
    score: float


def initialize_document_vector_collection() -> None:
    def initialize(client: QdrantClient) -> None:
        collection_name = settings.document_vector_collection_name

        if not client.collection_exists(collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=settings.document_embedding_dimension,
                    distance=models.Distance.COSINE,
                ),
            )

        client.create_payload_index(
            collection_name=collection_name,
            field_name="organization_id",
            field_schema=models.KeywordIndexParams(
                type=models.KeywordIndexType.KEYWORD,
                is_tenant=True,
            ),
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    _with_qdrant_client(initialize)


def upsert_document_chunk_vectors(
    *,
    chunks: Sequence[DocumentChunk],
    vectors: Sequence[list[float]],
) -> None:
    if len(chunks) != len(vectors):
        raise ValueError(
            "chunks and vectors must have the same length",
        )

    def upsert(client: QdrantClient) -> None:
        client.upsert(
            collection_name=settings.document_vector_collection_name,
            points=[
                models.PointStruct(
                    id=chunk.id,
                    vector=vector,
                    payload={
                        "organization_id": str(
                            chunk.organization_id,
                        ),
                        "document_id": str(chunk.document_id),
                        "chunk_index": chunk.chunk_index,
                        "index_version": chunk.index_version,
                    },
                )
                for chunk, vector in zip(
                    chunks,
                    vectors,
                    strict=True,
                )
            ],
        )

    _with_qdrant_client(upsert)


def search_document_chunk_vectors(
    *,
    organization_id: UUID,
    vector: list[float],
    limit: int,
    score_threshold: float,
) -> list[DocumentVectorSearchResult]:
    def search(
        client: QdrantClient,
    ) -> list[DocumentVectorSearchResult]:
        response = client.query_points(
            collection_name=settings.document_vector_collection_name,
            query=vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="organization_id",
                        match=models.MatchValue(
                            value=str(organization_id),
                        ),
                    ),
                ],
            ),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=False,
        )

        return [
            DocumentVectorSearchResult(
                chunk_id=UUID(str(point.id)),
                score=point.score,
            )
            for point in response.points
        ]

    return _with_qdrant_client(search)


def _with_qdrant_client(
    operation: Callable[[QdrantClient], Result],
) -> Result:
    client = QdrantClient(url=settings.qdrant_url)

    try:
        return operation(client)
    except (
        OSError,
        ResponseHandlingException,
        UnexpectedResponse,
    ) as exc:
        raise DocumentVectorStoreUnavailableError() from exc
    finally:
        client.close()


if __name__ == "__main__":
    initialize_document_vector_collection()