# Graph Report - CRUD  (2026-08-18)

## Corpus Check
- 155 files · ~37,502 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1074 nodes · 3150 edges · 84 communities (81 shown, 3 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 208 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `936c86b1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- exceptions.py
- Q: Как добавить настоящий upload pipeline Document после локального storage?
- models/users.py
- services/auth.py
- services/users.py
- Conversation
- evaluate_rag_baseline.py
- test_organizations.py
- OutboxMessage
- routers/organizations.py
- test_spa_preflight_allows_authorization_header
- crud
- test_conversations.py
- Agent Instructions
- AI Support Desk — Project Context
- Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?
- Q: Прочитай файл rules6.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям
- Q: Как добавить минимальный контракт Document в текущие SQLAlchemy models без нарушения tenant architecture?
- dependencies/organization_members.py
- routers/documents.py
- Q: Как безопасно подключить POST-загрузку документа к worker?
- test_users.py
- Q: Куда подключать загрузку документа в существующей архитектуре?
- document_search.py
- Q: Проверить миграцию create documents table
- enums.py
- document_processing.py
- routers/contacts.py
- Document-processing runbook
- Q: Прочитай файл .rules/rules8.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям, И ОБЬЯСНЯЙ НОВЫЕ ВЕЩИ КОТОРЫЕ ЕЩЕ НЕ БЫЛИ У НАС, ТИПО ЕСЛИ В КОДЕ ЧТОТО НОВОЕ ИСПОЛЬЗОВАЛ ОБЬЯНЯЙ ЕГО И ЗАЧЕМ ОНА НУЖНА
- test_document_api.py
- Q: Дальше
- Q: Прочитай rules6.md, проанализируй его и следуй его указаниям, объясняя все новые вещи
- Q: Дальше: разобрать существующий Docker стенд перед добавлением MinIO
- Q: Продолжить: подготовить точное изменение Compose для MinIO и объяснить новые понятия
- Q: Дать полный код для перехода FastAPI и worker с local DocumentStorage на MinIO
- Q: Не надо через каждый запрос тесты делать, я сам напишу когда нужно их делать. Просто идем дальше
- settings.py
- User
- test_auth.py
- test_security.py
- conftest.py
- document_text_extraction.py
- FastAPI
- Q: Продолжить неделю 15: разделить временную недоступность LLM и невалидный structured response, без добавления тестов.
- Q: Прочитай файл .rules/rules9.md и проанализируй его и следуй его указаниям чтобы помочь мне сделать этот проект и научиться новым вещам, объясняй новые вещи, которые ещё не были у нас.
- get_current_user
- Q: Идем дальше — начни следующий шаг недели 15 для надежного structured output document search.
- Q: Продолжить после разделения ошибок: добавить один repair-retry только для structured parsing и не ретраить citation/refusal.
- dependencies/auth.py
- login_user
- pagination.py
- test_auth_dependency.py
- run_async_migrations
- Settings
- ContactNotFoundError
- dependencies/documents.py
- dependencies/organizations.py
- .strip_email

## God Nodes (most connected - your core abstractions)
1. `User` - 68 edges
2. `Organization` - 46 edges
3. `Document` - 45 edges
4. `OrganizationRole` - 39 edges
5. `OrganizationMember` - 38 edges
6. `AppError` - 34 edges
7. `HttpErrorDetails` - 29 edges
8. `Conversation` - 28 edges
9. `Base` - 26 edges
10. `DocumentChunk` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_document_task_marks_permanent_error_without_retry()` --indirect_call--> `mark_failed()`  [INFERRED]
  tests/test_document_task.py → repositories/documents.py
- `HttpErrorDetails` --uses--> `AuthenticationRequiredError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `ContactNotFoundError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `DocumentNotFoundError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `DocumentSearchAnswerInvalidError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py

## Import Cycles
- None detected.

## Communities (84 total, 3 thin omitted)

### Community 0 - "exceptions.py"
Cohesion: 0.26
Nodes (22): HttpErrorDetails, AppError, ContactEmailAlreadyExistsError, ConversationAlreadyAssignedError, ConversationMemberRequiredError, ConversationNotFoundError, ConversationVersionConflictError, DocumentContentInvalidError (+14 more)

### Community 1 - "Q: Как добавить настоящий upload pipeline Document после локального storage?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как добавить настоящий upload pipeline Document после локального storage?, Source Nodes

### Community 2 - "models/users.py"
Cohesion: 0.29
Nodes (10): DeclarativeBase, Run migrations in 'offline' mode. This configures the context with just a URL…, run_migrations_offline(), Base, Contact, IdempotencyRecord, Message, get_by_key() (+2 more)

### Community 3 - "services/auth.py"
Cohesion: 0.18
Nodes (24): AuthenticationRequiredError, hash_password(), verify_password(), RefreshTokenCookie, get_by_id_for_update(), AsyncSession, UUID, logout_user() (+16 more)

### Community 4 - "services/users.py"
Cohesion: 0.08
Nodes (43): CurrentUserAccountDep, is_contact_email_unique_violation(), is_idempotency_record_organization_key_unique_violation(), is_organization_member_primary_key_violation(), is_user_email_unique_violation(), IntegrityError, put, get_current_user() (+35 more)

### Community 5 - "Conversation"
Cohesion: 0.06
Nodes (64): ConversationCreatePermissionDep, ConversationListPermissionDep, ConversationReadPermissionDep, ConversationUpdatePermissionDep, ConversationStatus, OrganizationPermission, get_existing_conversation(), ConversationFiltersQuery (+56 more)

### Community 6 - "evaluate_rag_baseline.py"
Cohesion: 0.21
Nodes (20): answer_matches_expected_terms(), build_summary(), evaluate(), evaluate_and_dispose_engine(), evaluate_case(), EvaluationCase, find_expected_chunk(), load_cases() (+12 more)

### Community 7 - "test_organizations.py"
Cohesion: 0.23
Nodes (38): OrganizationRole, OrganizationMember, create_stored_membership(), insert_stored_membership(), read_stored_membership(), authorization_headers(), create_organization(), create_user() (+30 more)

### Community 9 - "OutboxMessage"
Cohesion: 0.10
Nodes (32): OutboxMessage, list_pending_for_publish(), AsyncSession, publish_pending_messages(), Task, TaskPublisher, DocumentProcessingTask, fail_stale_processing_documents() (+24 more)

### Community 10 - "routers/organizations.py"
Cohesion: 0.07
Nodes (59): is_organization_slug_unique_violation(), get_redis(), Redis, Request, ExistingOrganizationMemberDep, ExistingUserDep, MemberCreatePermissionDep, MemberDeletePermissionDep (+51 more)

### Community 32 - "test_conversations.py"
Cohesion: 0.36
Nodes (28): authorization_headers(), create_contact(), create_conversation(), create_organization(), create_user(), async_sessionmaker, AsyncSession, MonkeyPatch (+20 more)

### Community 33 - "Agent Instructions"
Cohesion: 0.25
Nodes (7): Agent Instructions, Graphify, Implementation workflow, Project invariants, Repository hygiene, Skills and MCP, Tool routing

### Community 35 - "AI Support Desk — Project Context"
Cohesion: 0.33
Nodes (5): Agent guidance, AI Support Desk — Project Context, Architecture, Commands, Current Redis implementation

### Community 36 - "Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?, Source Nodes

### Community 37 - "Q: Прочитай файл rules6.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Прочитай файл rules6.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям, Source Nodes

### Community 38 - "Q: Как добавить минимальный контракт Document в текущие SQLAlchemy models без нарушения tenant architecture?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как добавить минимальный контракт Document в текущие SQLAlchemy models без нарушения tenant architecture?, Source Nodes

### Community 40 - "dependencies/organization_members.py"
Cohesion: 0.20
Nodes (18): LastOrganizationOwnerError, OrganizationPermissionDeniedError, get_current_organization_member(), get_existing_organization_member(), CurrentUserDep, SessionDep, UUID, require_organization_permission() (+10 more)

### Community 41 - "routers/documents.py"
Cohesion: 0.17
Nodes (23): DocumentCreatePermissionDep, DocumentReadPermissionDep, DocumentUploadFile, ExistingDocumentDep, get_document(), get_document_download_url(), list_documents(), CurrentUserDep (+15 more)

### Community 42 - "Q: Как безопасно подключить POST-загрузку документа к worker?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как безопасно подключить POST-загрузку документа к worker?, Source Nodes

### Community 43 - "test_users.py"
Cohesion: 0.25
Nodes (14): authorization_headers(), TestClient, UUID, register_user(), test_authenticated_user_id_validation(), test_health_check(), test_legacy_user_creation_is_disabled(), test_openapi_documents_redis_failure_responses() (+6 more)

### Community 45 - "Q: Куда подключать загрузку документа в существующей архитектуре?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Куда подключать загрузку документа в существующей архитектуре?, Source Nodes

### Community 46 - "document_search.py"
Cohesion: 0.09
Nodes (50): APIConnectionError, DocumentSearchAnswerInvalidError, DocumentSearchUnavailableError, get_learning_note(), LearningNoteArguments, main(), OpenAI, _build_input() (+42 more)

### Community 47 - "Q: Проверить миграцию create documents table"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Проверить миграцию create documents table, Source Nodes

### Community 48 - "enums.py"
Cohesion: 0.28
Nodes (10): DocumentStatus, MessageSenderType, StrEnum, create_completed_document_chunks(), async_sessionmaker, AsyncSession, MonkeyPatch, UUID (+2 more)

### Community 49 - "document_processing.py"
Cohesion: 0.07
Nodes (52): DocumentStorageUnavailableError, parametrize, claim_pending_for_processing(), get_by_id(), list_by_organization(), mark_completed(), mark_completed_as_failed(), mark_failed() (+44 more)

### Community 50 - "routers/contacts.py"
Cohesion: 0.17
Nodes (17): ContactCreatePermissionDep, ContactReadPermissionDep, ExistingContactDep, create_contact(), get_contact(), list_contacts(), ExistingOrganizationDep, get (+9 more)

### Community 51 - "Document-processing runbook"
Cohesion: 0.12
Nodes (15): Apply RAG code changes, Check database migrations, Check retry behavior safely, Document-processing runbook, Full verification before a commit, Inspect logs, Observe document indexing, Open Flower (+7 more)

### Community 52 - "Q: Прочитай файл .rules/rules8.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям, И ОБЬЯСНЯЙ НОВЫЕ ВЕЩИ КОТОРЫЕ ЕЩЕ НЕ БЫЛИ У НАС, ТИПО ЕСЛИ В КОДЕ ЧТОТО НОВОЕ ИСПОЛЬЗОВАЛ ОБЬЯНЯЙ ЕГО И ЗАЧЕМ ОНА НУЖНА"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Прочитай файл .rules/rules8.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям, И ОБЬЯСНЯЙ НОВЫЕ ВЕЩИ КОТОРЫЕ ЕЩЕ НЕ БЫЛИ У НАС, ТИПО ЕСЛИ В КОДЕ ЧТОТО НОВОЕ ИСПОЛЬЗОВАЛ ОБЬЯНЯЙ ЕГО И ЗАЧЕМ ОНА НУЖНА, Source Nodes

### Community 53 - "test_document_api.py"
Cohesion: 0.53
Nodes (8): create_organization(), create_stored_document(), async_sessionmaker, AsyncSession, TestClient, UUID, test_document_api_rejects_other_tenants_and_wrong_paths(), test_document_get_and_list_are_scoped_to_organization()

### Community 54 - "Q: Дальше"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Дальше, Source Nodes

### Community 55 - "Q: Прочитай rules6.md, проанализируй его и следуй его указаниям, объясняя все новые вещи"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Прочитай rules6.md, проанализируй его и следуй его указаниям, объясняя все новые вещи, Source Nodes

### Community 56 - "Q: Дальше: разобрать существующий Docker стенд перед добавлением MinIO"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Дальше: разобрать существующий Docker стенд перед добавлением MinIO, Source Nodes

### Community 57 - "Q: Продолжить: подготовить точное изменение Compose для MinIO и объяснить новые понятия"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Продолжить: подготовить точное изменение Compose для MinIO и объяснить новые понятия, Source Nodes

### Community 58 - "Q: Дать полный код для перехода FastAPI и worker с local DocumentStorage на MinIO"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Дать полный код для перехода FastAPI и worker с local DocumentStorage на MinIO, Source Nodes

### Community 59 - "Q: Не надо через каждый запрос тесты делать, я сам напишу когда нужно их делать. Просто идем дальше"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Не надо через каждый запрос тесты делать, я сам напишу когда нужно их делать. Просто идем дальше, Source Nodes

### Community 60 - "settings.py"
Cohesion: 0.13
Nodes (23): DocumentChunk, QdrantClient, list_completed_by_ids(), list_completed_without_index_version(), AsyncSession, UUID, replace_for_document(), Result (+15 more)

### Community 61 - "User"
Cohesion: 0.31
Nodes (15): Document, Organization, User, DisposableTestEngine, create_completed_document(), async_sessionmaker, AsyncSession, UUID (+7 more)

### Community 63 - "test_auth.py"
Cohesion: 0.20
Nodes (23): RefreshSession, read_stored_refresh_session(), TestClient, UUID, read_login_rate_limit(), register_alice(), test_failed_login_attempts_are_rate_limited(), test_login_falls_open_when_redis_is_unavailable() (+15 more)

### Community 64 - "test_security.py"
Cohesion: 0.23
Nodes (22): create_access_token(), create_refresh_token(), decode_access_token(), decode_refresh_token(), hash_refresh_token(), datetime, UUID, RefreshTokenClaims (+14 more)

### Community 65 - "conftest.py"
Cohesion: 0.16
Nodes (21): fixture, clean_client_cookies(), clean_database(), clear_database(), clear_redis_test_keys(), client(), concurrent_session_factory(), create_test_schema() (+13 more)

### Community 67 - "document_text_extraction.py"
Cohesion: 0.21
Nodes (26): _build_chunk_drafts(), _ChunkPart, _create_draft(), DocumentChunkDraft, _parts_length(), _split_blocks_into_parts(), _split_text(), _take_tail_parts() (+18 more)

### Community 68 - "FastAPI"
Cohesion: 0.21
Nodes (12): app_error_handler(), Request, FastAPI, JSONResponse, add_process_time_header(), health_check(), lifespan(), get (+4 more)

### Community 69 - "Q: Продолжить неделю 15: разделить временную недоступность LLM и невалидный structured response, без добавления тестов."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Продолжить неделю 15: разделить временную недоступность LLM и невалидный structured response, без добавления тестов., Source Nodes

### Community 70 - "Q: Прочитай файл .rules/rules9.md и проанализируй его и следуй его указаниям чтобы помочь мне сделать этот проект и научиться новым вещам, объясняй новые вещи, которые ещё не были у нас."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Прочитай файл .rules/rules9.md и проанализируй его и следуй его указаниям чтобы помочь мне сделать этот проект и научиться новым вещам, объясняй новые вещи, которые ещё не были у нас., Source Nodes

### Community 71 - "get_current_user"
Cohesion: 0.24
Nodes (10): bearer_scheme, get_current_user(), SessionDep, Depends, HTTPAuthorizationCredentials, get_active_by_email(), get_active_by_id(), list_active() (+2 more)

### Community 72 - "Q: Идем дальше — начни следующий шаг недели 15 для надежного structured output document search."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Идем дальше — начни следующий шаг недели 15 для надежного structured output document search., Source Nodes

### Community 73 - "Q: Продолжить после разделения ошибок: добавить один repair-retry только для structured parsing и не ретраить citation/refusal."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Продолжить после разделения ошибок: добавить один repair-retry только для structured parsing и не ретраить citation/refusal., Source Nodes

### Community 74 - "dependencies/auth.py"
Cohesion: 0.27
Nodes (8): UserNotFoundError, get_session(), AsyncSession, get_current_user_account(), get_existing_user(), CurrentUserDep, SessionDep, UUID

### Community 75 - "login_user"
Cohesion: 0.35
Nodes (10): login_user(), RedisDep, Request, clear_login_rate_limit(), enforce_login_ip_rate_limit(), enforce_login_rate_limit(), login_ip_rate_limit_key(), login_rate_limit_key() (+2 more)

### Community 76 - "pagination.py"
Cohesion: 0.25
Nodes (8): Cookie, get_pagination(), PaginationParams, BaseModel, Response, ge, le, Query

### Community 77 - "test_auth_dependency.py"
Cohesion: 0.57
Nodes (6): assert_authentication_required(), TestClient, test_current_user_rejects_invalid_token(), test_current_user_rejects_unknown_user(), test_current_user_requires_bearer_token(), test_current_user_returns_authenticated_user()

### Community 78 - "run_async_migrations"
Cohesion: 0.33
Nodes (6): Connection, do_run_migrations(), In this scenario we need to create an Engine and associate a connection with…, Run migrations in 'online' mode., run_async_migrations(), run_migrations_online()

### Community 79 - "Settings"
Cohesion: 0.40
Nodes (4): BaseSettings, Self, model_validator, Settings

### Community 80 - "ContactNotFoundError"
Cohesion: 0.60
Nodes (4): ContactNotFoundError, get_existing_contact(), SessionDep, UUID

### Community 81 - "dependencies/documents.py"
Cohesion: 0.60
Nodes (4): DocumentNotFoundError, get_existing_document(), SessionDep, UUID

### Community 82 - "dependencies/organizations.py"
Cohesion: 0.60
Nodes (4): OrganizationNotFoundError, get_existing_organization(), SessionDep, UUID

## Knowledge Gaps
- **77 isolated node(s):** `crud`, `Project invariants`, `Graphify`, `Skills and MCP`, `Implementation workflow` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `DocumentStorage` (9× useful, score=7.726129412)
- `Document` (7× useful, score=5.850950613)
- `services/documents.py` (5× useful, score=4.426723759)
- `Agent Instructions` (3× useful, score=2.714009832)
- `Implementation workflow` (3× useful, score=2.714009832)
- `Project invariants` (3× useful, score=2.714009832)
- `Architecture` (3× useful, score=2.714009832)
- `settings.py` (3× useful, score=2.647520323) _(code changed — re-verify)_
- `celery_app.py` (3× useful, score=2.547942602)
- `Organization` (3× useful, score=2.428378831)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_security.py`, `exceptions.py`, `models/users.py`, `services/auth.py`, `services/users.py`, `Conversation`, `conftest.py`, `test_organizations.py`, `get_current_user`, `dependencies/organization_members.py`, `dependencies/auth.py`, `routers/organizations.py`, `test_conversations.py`, `test_users.py`, `enums.py`, `document_processing.py`, `test_auth.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `Document` connect `User` to `exceptions.py`, `conftest.py`, `models/users.py`, `evaluate_rag_baseline.py`, `routers/documents.py`, `enums.py`, `dependencies/documents.py`, `document_processing.py`, `test_document_api.py`, `settings.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Organization` connect `User` to `exceptions.py`, `conftest.py`, `models/users.py`, `Conversation`, `test_organizations.py`, `dependencies/organization_members.py`, `routers/organizations.py`, `enums.py`, `document_processing.py`, `dependencies/organizations.py`, `routers/contacts.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `User` (e.g. with `Conversation` and `Document`) actually correct?**
  _`User` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Organization` (e.g. with `Contact` and `Conversation`) actually correct?**
  _`Organization` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Document` (e.g. with `DocumentChunk` and `DocumentStatus`) actually correct?**
  _`Document` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationRole` (e.g. with `OrganizationMember` and `OrganizationMemberListItem`) actually correct?**
  _`OrganizationRole` has 5 INFERRED edges - model-reasoned connections that need verification._