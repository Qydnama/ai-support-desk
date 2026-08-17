import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select

from core.enums import DocumentStatus
from database import engine, session_factory
from models.document_chunks import DocumentChunk
from models.documents import Document
from services import document_search
from services.document_embeddings import embed_document_texts
from services.document_vector_store import (
    search_document_chunk_vectors,
)
from settings import settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = (
    PROJECT_ROOT / "evaluations" / "rag_baseline" / "cases.json"
)


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    id: str
    question: str
    answer_expected: bool
    expected_document_filename: str | None
    expected_chunk_index: int | None
    expected_answer_terms: tuple[tuple[str, ...], ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate document RAG retrieval and citations.",
    )
    parser.add_argument(
        "--organization-id",
        required=True,
        type=UUID,
        help="Organization containing the uploaded evaluation corpus.",
    )
    parser.add_argument(
        "--top-k",
        default=5,
        type=int,
        help="Number of Qdrant candidates to evaluate.",
    )
    parser.add_argument(
        "--cases-path",
        default=DEFAULT_CASES_PATH,
        type=Path,
        help="Path to the JSON file containing evaluation cases.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON report.",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[EvaluationCase]:
    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported evaluation cases schema version.")

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Evaluation cases must contain a non-empty cases list.")

    cases: list[EvaluationCase] = []

    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise ValueError("Each evaluation case must be an object.")

        answer_expected = raw_case.get("answer_expected")
        if not isinstance(answer_expected, bool):
            raise ValueError("answer_expected must be true or false.")

        case_id = raw_case.get("id")
        question = raw_case.get("question")

        if not isinstance(case_id, str) or not case_id:
            raise ValueError("Each evaluation case needs a non-empty id.")

        if not isinstance(question, str) or not question:
            raise ValueError("Each evaluation case needs a non-empty question.")

        filename = raw_case.get("expected_document_filename")
        chunk_index = raw_case.get("expected_chunk_index")
        raw_answer_terms = raw_case.get(
            "expected_answer_terms",
            [],
        )

        if answer_expected:
            if not isinstance(filename, str) or not filename:
                raise ValueError(
                    f"Case {case_id} needs expected_document_filename.",
                )
            if not isinstance(chunk_index, int) or chunk_index < 0:
                raise ValueError(
                    f"Case {case_id} needs expected_chunk_index.",
                )
            if (
                not isinstance(raw_answer_terms, list)
                or not raw_answer_terms
            ):
                raise ValueError(
                    f"Case {case_id} needs expected_answer_terms.",
                )
        elif any(
            value is not None
            for value in (filename, chunk_index)
        ) or raw_answer_terms:
            raise ValueError(
                f"Case {case_id} must not define expected sources or terms.",
            )

        answer_terms = _parse_expected_answer_terms(
            case_id=case_id,
            raw_answer_terms=raw_answer_terms,
        )

        cases.append(
            EvaluationCase(
                id=case_id,
                question=question,
                answer_expected=answer_expected,
                expected_document_filename=filename,
                expected_chunk_index=chunk_index,
                expected_answer_terms=tuple(answer_terms),
            ),
        )

    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Evaluation case ids must be unique.")

    return cases


def _parse_expected_answer_terms(
    *,
    case_id: str,
    raw_answer_terms: list[Any],
) -> tuple[tuple[str, ...], ...]:
    """Turn each required term into one or more acceptable variants."""
    parsed_groups: list[tuple[str, ...]] = []

    for raw_term in raw_answer_terms:
        variants = [raw_term] if isinstance(raw_term, str) else raw_term

        if (
            not isinstance(variants, list)
            or not variants
            or not all(
                isinstance(variant, str) and variant
                for variant in variants
            )
        ):
            raise ValueError(
                f"Case {case_id} has an invalid expected_answer_terms entry.",
            )

        parsed_groups.append(tuple(variants))

    return tuple(parsed_groups)


def answer_matches_expected_terms(
    *,
    answer: str,
    expected_answer_terms: tuple[tuple[str, ...], ...],
) -> bool:
    answer_text = answer.casefold()

    return all(
        any(
            variant.casefold() in answer_text
            for variant in variants
        )
        for variants in expected_answer_terms
    )


async def find_expected_chunk(
    *,
    organization_id: UUID,
    case: EvaluationCase,
) -> DocumentChunk:
    async with session_factory() as session:
        chunks = await session.scalars(
            select(DocumentChunk)
            .join(DocumentChunk.document)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.chunk_index == case.expected_chunk_index,
                DocumentChunk.index_version
                == settings.document_chunk_index_version,
                Document.organization_id == organization_id,
                Document.original_filename
                == case.expected_document_filename,
                Document.status == DocumentStatus.COMPLETED,
            ),
        )
        matches = list(chunks)

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one completed chunk for "
            f"case={case.id}, filename={case.expected_document_filename}, "
            f"chunk_index={case.expected_chunk_index}; found {len(matches)}.",
        )

    return matches[0]


async def evaluate_case(
    *,
    organization_id: UUID,
    case: EvaluationCase,
    top_k: int,
) -> dict[str, Any]:
    expected_chunk: DocumentChunk | None = None
    retrieval_rank: int | None = None

    if case.answer_expected:
        expected_chunk = await find_expected_chunk(
            organization_id=organization_id,
            case=case,
        )
        question_vector = (
            await asyncio.to_thread(
                embed_document_texts,
                [case.question],
            )
        )[0]
        candidates = await asyncio.to_thread(
            search_document_chunk_vectors,
            organization_id=organization_id,
            vector=question_vector,
            limit=top_k,
            score_threshold=settings.document_search_score_threshold,
        )

        retrieval_rank = next(
            (
                index
                for index, candidate in enumerate(candidates, start=1)
                if candidate.chunk_id == expected_chunk.id
            ),
            None,
        )

    async with session_factory() as session:
        result = await document_search.search_documents(
            session=session,
            organization_id=organization_id,
            question=case.question,
            limit=top_k,
        )

    answer = result.answer or ""
    citation_chunk_ids = [
        str(citation.chunk_id)
        for citation in result.citations
    ]

    report: dict[str, Any] = {
        "id": case.id,
        "question": case.question,
        "answer_expected": case.answer_expected,
        "answer": result.answer,
        "answer_not_found": result.answer_not_found,
        "citation_chunk_ids": citation_chunk_ids,
    }

    if not case.answer_expected:
        report["abstention_correct"] = (
            result.answer_not_found
            and not result.citations
        )
        return report

    assert expected_chunk is not None

    report.update(
        {
            "expected_chunk_id": str(expected_chunk.id),
            "retrieval_rank": retrieval_rank,
            "retrieval_hit_at_k": retrieval_rank is not None,
            "citation_correct": (
                str(expected_chunk.id) in citation_chunk_ids
            ),
            "answer_terms_correct": (
                not result.answer_not_found
                and answer_matches_expected_terms(
                    answer=answer,
                    expected_answer_terms=(
                        case.expected_answer_terms
                    ),
                )
            ),
        },
    )
    return report


def rate(*, successes: int, total: int) -> float | None:
    if not total:
        return None

    return round(successes / total, 3)


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    positive_results = [
        result
        for result in results
        if result["answer_expected"]
    ]
    negative_results = [
        result
        for result in results
        if not result["answer_expected"]
    ]

    return {
        "positive_case_count": len(positive_results),
        "negative_case_count": len(negative_results),
        "recall_at_k": rate(
            successes=sum(
                result["retrieval_hit_at_k"]
                for result in positive_results
            ),
            total=len(positive_results),
        ),
        "citation_correctness": rate(
            successes=sum(
                result["citation_correct"]
                for result in positive_results
            ),
            total=len(positive_results),
        ),
        "answer_term_correctness": rate(
            successes=sum(
                result["answer_terms_correct"]
                for result in positive_results
            ),
            total=len(positive_results),
        ),
        "abstention_correctness": rate(
            successes=sum(
                result["abstention_correct"]
                for result in negative_results
            ),
            total=len(negative_results),
        ),
    }


async def evaluate(
    *,
    organization_id: UUID,
    cases: list[EvaluationCase],
    top_k: int,
) -> dict[str, Any]:
    if top_k < 1 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20.")

    results = [
        await evaluate_case(
            organization_id=organization_id,
            case=case,
            top_k=top_k,
        )
        for case in cases
    ]

    return {
        "organization_id": str(organization_id),
        "index_version": settings.document_chunk_index_version,
        "top_k": top_k,
        "summary": build_summary(results),
        "cases": results,
    }


async def evaluate_and_dispose_engine(
    *,
    organization_id: UUID,
    cases: list[EvaluationCase],
    top_k: int,
) -> dict[str, Any]:
    try:
        return await evaluate(
            organization_id=organization_id,
            cases=cases,
            top_k=top_k,
        )
    finally:
        await engine.dispose()


def main() -> None:
    args = parse_args()
    cases = load_cases(args.cases_path)
    report = asyncio.run(
        evaluate_and_dispose_engine(
            organization_id=args.organization_id,
            cases=cases,
            top_k=args.top_k,
        ),
    )

    serialized_report = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            serialized_report + "\n",
            encoding="utf-8",
        )

    print(serialized_report)


if __name__ == "__main__":
    main()
