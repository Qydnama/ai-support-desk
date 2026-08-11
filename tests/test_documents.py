import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums import DocumentStatus
from models.documents import Document
from models.organizations import Organization
from models.users import User
from repositories import documents as document_repository


def test_document_is_tenant_scoped_and_starts_pending(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization_id = uuid4()
    user_id = uuid4()
    document_id = uuid4()

    async def create_and_read_document() -> Document:
        async with concurrent_session_factory() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        name="Document uploader",
                        email="uploader@example.com",
                    ),
                    Organization(
                        id=organization_id,
                        name="Document organization",
                        slug="document-organization",
                    ),
                    Document(
                        id=document_id,
                        organization_id=organization_id,
                        uploaded_by_user_id=user_id,
                        original_filename="policy.txt",
                        content_type="text/plain",
                        storage_key="documents/policy.txt",
                    ),
                ],
            )
            await session.commit()

        async with concurrent_session_factory() as session:
            document = await session.scalar(
                select(Document).where(Document.id == document_id),
            )

        assert document is not None
        return document

    document = asyncio.run(create_and_read_document())

    assert document.organization_id == organization_id
    assert document.uploaded_by_user_id == user_id
    assert document.status == DocumentStatus.PENDING
    assert document.extracted_text is None
    assert document.error_message is None
    assert document.processing_started_at is None


def test_document_storage_key_is_unique(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization_id = uuid4()
    user_id = uuid4()

    async def create_duplicate_storage_keys() -> None:
        async with concurrent_session_factory() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        name="Storage uploader",
                        email="storage-uploader@example.com",
                    ),
                    Organization(
                        id=organization_id,
                        name="Storage organization",
                        slug="storage-organization",
                    ),
                ],
            )
            await session.commit()

        async with concurrent_session_factory() as session:
            session.add_all(
                [
                    Document(
                        id=uuid4(),
                        organization_id=organization_id,
                        uploaded_by_user_id=user_id,
                        original_filename="first.txt",
                        content_type="text/plain",
                        storage_key="documents/shared-key.txt",
                    ),
                    Document(
                        id=uuid4(),
                        organization_id=organization_id,
                        uploaded_by_user_id=user_id,
                        original_filename="second.txt",
                        content_type="text/plain",
                        storage_key="documents/shared-key.txt",
                    ),
                ],
            )

            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
            else:
                raise AssertionError("duplicate storage keys must be rejected")

    asyncio.run(create_duplicate_storage_keys())


def test_document_repository_is_tenant_scoped(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_organization_id = uuid4()
    second_organization_id = uuid4()
    first_user_id = uuid4()
    second_user_id = uuid4()
    first_document_id = uuid4()
    second_document_id = uuid4()

    async def create_and_query_documents() -> tuple[
        Document | None,
        Document | None,
        list[Document],
    ]:
        async with concurrent_session_factory() as session:
            session.add_all(
                [
                    User(
                        id=first_user_id,
                        name="First document uploader",
                        email="first-uploader@example.com",
                    ),
                    User(
                        id=second_user_id,
                        name="Second document uploader",
                        email="second-uploader@example.com",
                    ),
                    Organization(
                        id=first_organization_id,
                        name="First document organization",
                        slug="first-document-organization",
                    ),
                    Organization(
                        id=second_organization_id,
                        name="Second document organization",
                        slug="second-document-organization",
                    ),
                ],
            )
            await session.commit()

        async with concurrent_session_factory() as session:
            session.add_all(
                [
                    Document(
                        id=first_document_id,
                        organization_id=first_organization_id,
                        uploaded_by_user_id=first_user_id,
                        original_filename="first.txt",
                        content_type="text/plain",
                        storage_key="documents/first.txt",
                    ),
                    Document(
                        id=second_document_id,
                        organization_id=second_organization_id,
                        uploaded_by_user_id=second_user_id,
                        original_filename="second.txt",
                        content_type="text/plain",
                        storage_key="documents/second.txt",
                    ),
                ],
            )
            await session.commit()

        async with concurrent_session_factory() as session:
            own_document = await document_repository.get_by_id(
                session,
                document_id=first_document_id,
                organization_id=first_organization_id,
            )
            foreign_document = await document_repository.get_by_id(
                session,
                document_id=first_document_id,
                organization_id=second_organization_id,
            )
            second_organization_documents = (
                await document_repository.list_by_organization(
                    session,
                    organization_id=second_organization_id,
                    limit=10,
                    offset=0,
                )
            )

        return (
            own_document,
            foreign_document,
            second_organization_documents,
        )

    own_document, foreign_document, second_organization_documents = (
        asyncio.run(create_and_query_documents())
    )

    assert own_document is not None
    assert own_document.id == first_document_id
    assert foreign_document is None
    assert [document.id for document in second_organization_documents] == [
        second_document_id,
    ]
