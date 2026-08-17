from collections.abc import Sequence

from openai import (
    APIConnectionError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from settings import settings


class DocumentEmbeddingUnavailableError(OSError):
    """OpenAI temporarily cannot create embeddings."""


def embed_document_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []

    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
    )

    try:
        response = client.embeddings.create(
            model=settings.document_embedding_model,
            input=list(texts),
            dimensions=settings.document_embedding_dimension,
        )
    except (
        APIConnectionError,
        InternalServerError,
        RateLimitError,
    ) as error:
        raise DocumentEmbeddingUnavailableError(
            "OpenAI embeddings service is temporarily unavailable."
        ) from error

    embeddings_by_index = {
        embedding.index: embedding.embedding
        for embedding in response.data
    }

    vectors = [
        embeddings_by_index[index]
        for index in range(len(texts))
    ]

    if len(vectors) != len(texts):
        raise ValueError(
            "OpenAI returned an unexpected number of embeddings."
        )

    if any(
        len(vector) != settings.document_embedding_dimension
        for vector in vectors
    ):
        raise ValueError(
            "OpenAI returned embeddings with an unexpected dimension."
        )

    return vectors