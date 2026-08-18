import httpx
import pytest

from openai import APIConnectionError

from services import document_answer_provider
from services.document_answer_provider import GeneratedDocumentAnswer


class FakeResponses:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


class FakeClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


class FakeParsedResponse:
    def __init__(
        self,
        answer: GeneratedDocumentAnswer,
    ) -> None:
        self.output_parsed = answer


def transient_connection_error() -> APIConnectionError:
    return APIConnectionError(
        message="Temporary connection error.",
        request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
    )


def test_provider_retries_temporary_primary_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_answer = GeneratedDocumentAnswer(
        answer="Refunds are available within 30 days.",
        answer_not_found=False,
        citation_numbers=[1],
    )
    responses = FakeResponses(
        [
            transient_connection_error(),
            FakeParsedResponse(generated_answer),
        ],
    )
    delays: list[float] = []

    monkeypatch.setattr(
        document_answer_provider,
        "OpenAI",
        lambda **_: FakeClient(responses),
    )
    monkeypatch.setattr(
        document_answer_provider.time,
        "sleep",
        delays.append,
    )

    result = document_answer_provider.request_document_answer(
        instructions="Use only supplied sources.",
        input_text="Question: When can I request a refund?",
    )

    assert result == generated_answer
    assert delays == [0.5]
    assert [call["model"] for call in responses.calls] == [
        "gpt-5.6-luna",
        "gpt-5.6-luna",
    ]


def test_provider_uses_fallback_after_primary_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_answer = GeneratedDocumentAnswer(
        answer="Refunds are available within 30 days.",
        answer_not_found=False,
        citation_numbers=[1],
    )
    responses = FakeResponses(
        [
            transient_connection_error(),
            transient_connection_error(),
            FakeParsedResponse(generated_answer),
        ],
    )
    delays: list[float] = []

    monkeypatch.setattr(
        document_answer_provider,
        "OpenAI",
        lambda **_: FakeClient(responses),
    )
    monkeypatch.setattr(
        document_answer_provider.time,
        "sleep",
        delays.append,
    )

    result = document_answer_provider.request_document_answer(
        instructions="Use only supplied sources.",
        input_text="Question: When can I request a refund?",
    )

    assert result == generated_answer
    assert delays == [0.5]
    assert [call["model"] for call in responses.calls] == [
        "gpt-5.6-luna",
        "gpt-5.6-luna",
        "gpt-5.6-terra",
    ]
