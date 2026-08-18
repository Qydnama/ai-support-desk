import logging
import time

from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, Field

from settings import settings

logger = logging.getLogger(__name__)

MAX_TRANSIENT_ATTEMPTS = 2
TRANSIENT_RETRY_BASE_DELAY_SECONDS = 0.5

TRANSIENT_PROVIDER_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)


class DocumentAnswerProviderUnavailableError(OSError):
    """The configured LLM provider is temporarily unavailable."""


class DocumentAnswerProviderInvalidResponseError(Exception):
    """The LLM provider returned an invalid structured response."""


class GeneratedDocumentAnswer(BaseModel):
    answer: str | None = Field(
        default=None,
        max_length=4_000,
    )
    answer_not_found: bool
    citation_numbers: list[int] = Field(
        default_factory=list,
        max_length=20,
    )


def request_document_answer(
    *,
    instructions: str,
    input_text: str,
) -> GeneratedDocumentAnswer | None:
    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        max_retries=0,
    )

    try:
        return _request_document_answer_from_model(
            client=client,
            model=settings.document_answer_model,
            instructions=instructions,
            input_text=input_text,
        )
    except DocumentAnswerProviderUnavailableError as error:
        logger.warning(
            "document_answer_provider_fallback "
            "primary_model=%s fallback_model=%s error_type=%s",
            settings.document_answer_model,
            settings.document_answer_fallback_model,
            error.__cause__.__class__.__name__
            if error.__cause__ is not None
            else error.__class__.__name__,
        )

        return _request_document_answer_from_model(
            client=client,
            model=settings.document_answer_fallback_model,
            instructions=instructions,
            input_text=input_text,
        )


def _request_document_answer_from_model(
    *,
    client: OpenAI,
    model: str,
    instructions: str,
    input_text: str,
) -> GeneratedDocumentAnswer | None:
    for attempt_number in range(1, MAX_TRANSIENT_ATTEMPTS + 1):
        try:
            response = client.responses.parse(
                model=model,
                instructions=instructions,
                input=input_text,
                text_format=GeneratedDocumentAnswer,
                reasoning={
                    "effort": (
                        settings.document_answer_reasoning_effort
                    ),
                },
                text={
                    "verbosity": "low",
                },
                max_output_tokens=(
                    settings.document_answer_max_output_tokens
                ),
                store=False,
            )
        except APIResponseValidationError as error:
            raise DocumentAnswerProviderInvalidResponseError(
                "The LLM provider returned an invalid response."
            ) from error
        except TRANSIENT_PROVIDER_ERRORS as error:
            if attempt_number == MAX_TRANSIENT_ATTEMPTS:
                raise DocumentAnswerProviderUnavailableError(
                    "The LLM provider is temporarily unavailable."
                ) from error

            delay_seconds = (
                TRANSIENT_RETRY_BASE_DELAY_SECONDS
                * 2 ** (attempt_number - 1)
            )

            logger.warning(
                "document_answer_provider_retry model=%s attempt=%s "
                "max_attempts=%s delay_seconds=%s error_type=%s",
                model,
                attempt_number,
                MAX_TRANSIENT_ATTEMPTS,
                delay_seconds,
                error.__class__.__name__,
            )

            time.sleep(delay_seconds)
        else:
            return response.output_parsed

    raise AssertionError("The retry loop ended unexpectedly.")