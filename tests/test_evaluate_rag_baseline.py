import json

import pytest

from scripts.evaluate_rag_baseline import (
    answer_matches_expected_terms,
    load_cases,
)


def test_answer_terms_accept_alternative_word_forms() -> None:
    assert answer_matches_expected_terms(
        answer="О подозрении нужно сообщить в течение одного часа.",
        expected_answer_terms=(
            ("один час", "одного часа"),
        ),
    )


def test_load_cases_supports_alternative_term_variants(
    tmp_path,
) -> None:
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "id": "response_time",
                        "question": "When is the response due?",
                        "answer_expected": True,
                        "expected_document_filename": "policy.txt",
                        "expected_chunk_index": 0,
                        "expected_answer_terms": [
                            ["one hour", "an hour"],
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    case = load_cases(cases_path)[0]

    assert case.expected_answer_terms == (
        ("one hour", "an hour"),
    )


def test_load_cases_rejects_empty_term_variant_group(
    tmp_path,
) -> None:
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "id": "response_time",
                        "question": "When is the response due?",
                        "answer_expected": True,
                        "expected_document_filename": "policy.txt",
                        "expected_chunk_index": 0,
                        "expected_answer_terms": [[]],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid expected_answer_terms"):
        load_cases(cases_path)
