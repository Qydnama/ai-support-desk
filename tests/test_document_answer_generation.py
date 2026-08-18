import pytest

from services import document_answer_generation
from services.document_answer_generation import (
    DocumentAnswerGenerationStructuredOutputError,
    DocumentAnswerGenerationValidationError,
    GeneratedDocumentAnswer,
)
from services.document_answer_provider import (
    DocumentAnswerProviderInvalidResponseError,
)


def test_generation_retries_once_after_invalid_structured_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, str]] = []

    def request_document_answer(
        *,
        instructions: str,
        input_text: str,
    ) -> GeneratedDocumentAnswer:
        calls.append(
            {
                "instructions": instructions,
                "input_text": input_text,
            },
        )

        if len(calls) == 1:
            raise DocumentAnswerProviderInvalidResponseError(
                "Invalid structured response.",
            )

        return GeneratedDocumentAnswer(
            answer="Refunds are available within 30 days.",
            answer_not_found=False,
            citation_numbers=[1],
        )

    monkeypatch.setattr(
        document_answer_generation,
        "request_document_answer",
        request_document_answer,
    )

    result = document_answer_generation.generate_document_answer(
        question="When can I request a refund?",
        source_texts=["Refunds are available within 30 days."],
    )

    assert result.answer_not_found is False
    assert len(calls) == 2
    assert calls[0]["instructions"] == (
        document_answer_generation.INSTRUCTIONS
    )
    assert calls[1]["instructions"] == (
        document_answer_generation.REPAIR_INSTRUCTIONS
    )
    assert calls[0]["input_text"] == calls[1]["input_text"]


def test_generation_stops_after_second_invalid_structured_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def request_document_answer(
        *,
        instructions: str,
        input_text: str,
    ) -> GeneratedDocumentAnswer:
        nonlocal calls
        calls += 1
        raise DocumentAnswerProviderInvalidResponseError(
            "Invalid structured response.",
        )

    monkeypatch.setattr(
        document_answer_generation,
        "request_document_answer",
        request_document_answer,
    )

    with pytest.raises(DocumentAnswerGenerationStructuredOutputError):
        document_answer_generation.generate_document_answer(
            question="When can I request a refund?",
            source_texts=["Refunds are available within 30 days."],
        )

    assert calls == 2


def test_generation_does_not_retry_invalid_citation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def request_document_answer(
        *,
        instructions: str,
        input_text: str,
    ) -> GeneratedDocumentAnswer:
        nonlocal calls
        calls += 1

        return GeneratedDocumentAnswer(
            answer="Refunds are available within 30 days.",
            answer_not_found=False,
            citation_numbers=[2],
        )

    monkeypatch.setattr(
        document_answer_generation,
        "request_document_answer",
        request_document_answer,
    )

    with pytest.raises(DocumentAnswerGenerationValidationError):
        document_answer_generation.generate_document_answer(
            question="When can I request a refund?",
            source_texts=["Refunds are available within 30 days."],
        )

    assert calls == 1

