from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    jwt_secret: SecretStr = Field(
        min_length=32,
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(
        default=15,
        ge=1,
        le=60,
    )
    refresh_cookie_name: str
    refresh_cookie_secure: bool
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=90,
    )

    redis_url: str
    redis_test_url: str
    login_rate_limit_max_attempts: int = Field(
        default=5,
        ge=1,
        le=100,
    )
    login_rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3_600,
    )
    login_ip_rate_limit_max_attempts: int = Field(
        default=30,
        ge=1,
        le=1_000,
    )
    login_ip_rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3_600,
    )

    celery_broker_url: str
    celery_result_backend: str

    minio_endpoint: str
    minio_public_endpoint: str
    minio_access_key: SecretStr
    minio_secret_key: SecretStr
    minio_secure: bool = False
    minio_public_secure: bool = False
    minio_documents_bucket: str
    minio_presigned_get_expires_seconds: int = Field(
        default=300,
        ge=60,
        le=3_600,
    )

    document_upload_max_bytes: int = Field(
        default=1_048_576,
        ge=1,
        le=10_485_760,
    )
    document_pdf_max_pages: int = Field(
        default=100,
        ge=1,
        le=1_000,
    )
    document_pdf_max_page_content_bytes: int = Field(
        default=5_242_880,
        ge=1,
        le=52_428_800,
    )
    document_docx_max_paragraphs: int = Field(
        default=10_000,
        ge=1,
        le=100_000,
    )
    document_docx_max_uncompressed_bytes: int = Field(
        default=20_971_520,
        ge=1,
        le=104_857_600,
    )
    document_extracted_text_max_chars: int = Field(
        default=1_000_000,
        ge=1,
        le=10_000_000,
    )
    document_processing_stale_after_seconds: int = Field(
        default=600,
        ge=60,
        le=86_400,
    )
    document_maintenance_interval_seconds: int = Field(
        default=60,
        ge=10,
        le=3_600,
    )
    document_chunk_max_chars: int = Field(
        default=1_200,
        ge=100,
        le=10_000,
    )
    document_chunk_overlap_chars: int = Field(
        default=200,
        ge=0,
        le=2_000,
    )
    document_chunk_index_version: str = Field(
        default="v2",
        min_length=1,
        max_length=64,
    )
    document_embedding_model: Literal["text-embedding-3-small"] = (
        "text-embedding-3-small"
    )
    document_embedding_dimension: int = Field(
        default=1_536,
        ge=1,
    )
    openai_api_key: SecretStr
    document_vector_collection_name: str = Field(
        default="document_chunks_v2",
        min_length=1,
        max_length=255,
    )
    qdrant_url: str = "http://localhost:6333"
    outbox_publish_batch_size: int = Field(
        default=100,
        ge=1,
        le=1_000,
    )
    outbox_publish_interval_seconds: int = Field(
        default=10,
        ge=1,
        le=3_600,
    )
    document_search_score_threshold: float = Field(
        default=0.1,
        ge=-1.0,
        le=1.0,
    )
    document_answer_model: Literal["gpt-5.6-luna"] = (
        "gpt-5.6-luna"
    )
    document_answer_fallback_model: Literal["gpt-5.6-terra"] = (
        "gpt-5.6-terra"
    )
    document_answer_reasoning_effort: Literal["none", "low"] = (
        "none"
    )
    document_answer_max_output_tokens: int = Field(
        default=500,
        ge=50,
        le=2_000,
    )
    

    @model_validator(mode="after")
    def validate_document_chunk_settings(self) -> Self:
        if (
            self.document_chunk_overlap_chars
            >= self.document_chunk_max_chars
        ):
            raise ValueError(
                "document_chunk_overlap_chars must be smaller "
                "than document_chunk_max_chars",
            )

        return self

settings = Settings()
