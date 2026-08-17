# Graph Report - CRUD  (2026-08-18)

## Corpus Check
- 149 files · ~36,496 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1015 nodes · 3015 edges · 72 communities (69 shown, 3 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 181 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21d4d90b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- evaluate_rag_baseline.py
- Q: Как добавить настоящий upload pipeline Document после локального storage?
- User
- test_auth.py
- services/users.py
- routers/conversations.py
- services/auth.py
- test_organizations.py
- OutboxMessage
- services/organizations.py
- test_spa_preflight_allows_authorization_header
- crud
- test_conversations.py
- Agent Instructions
- AI Support Desk — Project Context
- Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?
- Q: Прочитай файл rules6.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям
- Q: Как добавить минимальный контракт Document в текущие SQLAlchemy models без нарушения tenant architecture?
- exceptions.py
- routers/documents.py
- Q: Как безопасно подключить POST-загрузку документа к worker?
- test_users.py
- Q: Куда подключать загрузку документа в существующей архитектуре?
- test_security.py
- Q: Проверить миграцию create documents table
- login_user
- test_document_minio_integration.py
- services/contacts.py
- Document-processing runbook
- Q: Прочитай файл .rules/rules8.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям, И ОБЬЯСНЯЙ НОВЫЕ ВЕЩИ КОТОРЫЕ ЕЩЕ НЕ БЫЛИ У НАС, ТИПО ЕСЛИ В КОДЕ ЧТОТО НОВОЕ ИСПОЛЬЗОВАЛ ОБЬЯНЯЙ ЕГО И ЗАЧЕМ ОНА НУЖНА
- test_document_api.py
- Q: Дальше
- Q: Прочитай rules6.md, проанализируй его и следуй его указаниям, объясняя все новые вещи
- Q: Дальше: разобрать существующий Docker стенд перед добавлением MinIO
- Q: Продолжить: подготовить точное изменение Compose для MinIO и объяснить новые понятия
- Q: Дать полный код для перехода FastAPI и worker с local DocumentStorage на MinIO
- Q: Не надо через каждый запрос тесты делать, я сам напишу когда нужно их делать. Просто идем дальше
- test_auth_dependency.py
- get_current_user
- routers/organizations.py
- .strip_email
- OrganizationMember
- settings.py
- services/conversations.py
- dependencies/conversations.py
- app_error_handler
- get_pagination

## God Nodes (most connected - your core abstractions)
1. `User` - 68 edges
2. `Organization` - 46 edges
3. `Document` - 45 edges
4. `OrganizationRole` - 39 edges
5. `OrganizationMember` - 38 edges
6. `AppError` - 33 edges
7. `HttpErrorDetails` - 28 edges
8. `Conversation` - 28 edges
9. `Base` - 26 edges
10. `DocumentChunk` - 25 edges

## Surprising Connections (you probably didn't know these)
- `HttpErrorDetails` --uses--> `AuthenticationRequiredError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `ContactNotFoundError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `DocumentSearchUnavailableError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `DocumentStorageUnavailableError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `LastOrganizationOwnerError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py

## Import Cycles
- None detected.

## Communities (72 total, 3 thin omitted)

### Community 0 - "evaluate_rag_baseline.py"
Cohesion: 0.09
Nodes (43): DocumentSearchUnavailableError, QdrantClient, Result, answer_matches_expected_terms(), build_summary(), evaluate(), evaluate_and_dispose_engine(), evaluate_case() (+35 more)

### Community 1 - "Q: Как добавить настоящий upload pipeline Document после локального storage?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как добавить настоящий upload pipeline Document после локального storage?, Source Nodes

### Community 2 - "User"
Cohesion: 0.07
Nodes (78): Connection, DocumentStatus, MessageSenderType, DeclarativeBase, fixture, do_run_migrations(), Run migrations in 'offline' mode. This configures the context with just a URL…, In this scenario we need to create an Engine and associate a connection with… (+70 more)

### Community 3 - "test_auth.py"
Cohesion: 0.20
Nodes (23): RefreshSession, read_stored_refresh_session(), TestClient, UUID, read_login_rate_limit(), register_alice(), test_failed_login_attempts_are_rate_limited(), test_login_falls_open_when_redis_is_unavailable() (+15 more)

### Community 4 - "services/users.py"
Cohesion: 0.12
Nodes (30): CurrentUserAccountDep, is_user_email_unique_violation(), put, get_current_user(), CurrentUserDep, get, delete_user(), get_user() (+22 more)

### Community 5 - "routers/conversations.py"
Cohesion: 0.09
Nodes (41): ConversationCreatePermissionDep, ConversationListPermissionDep, ConversationReadPermissionDep, ConversationUpdatePermissionDep, ConversationStatus, ExistingConversationDep, IdempotencyKeyHeader, MessageCreatePermissionDep (+33 more)

### Community 6 - "services/auth.py"
Cohesion: 0.18
Nodes (24): AuthenticationRequiredError, hash_password(), verify_password(), RefreshTokenCookie, get_by_id_for_update(), AsyncSession, UUID, logout_user() (+16 more)

### Community 7 - "test_organizations.py"
Cohesion: 0.24
Nodes (36): OrganizationRole, create_stored_membership(), read_stored_membership(), authorization_headers(), create_organization(), create_user(), default_owner_headers(), delete_cached_value() (+28 more)

### Community 9 - "OutboxMessage"
Cohesion: 0.17
Nodes (23): OutboxMessage, list_pending_for_publish(), AsyncSession, publish_pending_messages(), TaskPublisher, test_outbox_publisher_task_runs_service(), configure_document_upload(), create_organization() (+15 more)

### Community 10 - "services/organizations.py"
Cohesion: 0.07
Nodes (52): is_organization_slug_unique_violation(), ExistingOrganizationMemberDep, ExistingUserDep, MemberCreatePermissionDep, MemberDeletePermissionDep, MemberReadPermissionDep, MemberRoleUpdatePermissionDep, OrganizationDeletePermissionDep (+44 more)

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

### Community 40 - "exceptions.py"
Cohesion: 0.25
Nodes (23): HttpErrorDetails, AppError, ContactEmailAlreadyExistsError, ConversationAlreadyAssignedError, ConversationMemberRequiredError, ConversationNotFoundError, ConversationVersionConflictError, DocumentContentInvalidError (+15 more)

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

### Community 46 - "test_security.py"
Cohesion: 0.23
Nodes (22): create_access_token(), create_refresh_token(), decode_access_token(), decode_refresh_token(), hash_refresh_token(), datetime, UUID, RefreshTokenClaims (+14 more)

### Community 47 - "Q: Проверить миграцию create documents table"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Проверить миграцию create documents table, Source Nodes

### Community 48 - "login_user"
Cohesion: 0.35
Nodes (10): login_user(), RedisDep, Request, clear_login_rate_limit(), enforce_login_ip_rate_limit(), enforce_login_rate_limit(), login_ip_rate_limit_key(), login_rate_limit_key() (+2 more)

### Community 49 - "test_document_minio_integration.py"
Cohesion: 0.10
Nodes (26): DocumentStorageUnavailableError, parametrize, create_document_storage_key(), DocumentStorage, get_document_storage(), MinioDocumentStorage, Path, UUID (+18 more)

### Community 50 - "services/contacts.py"
Cohesion: 0.11
Nodes (27): ContactCreatePermissionDep, ContactReadPermissionDep, is_contact_email_unique_violation(), ExistingContactDep, create_contact(), get_contact(), list_contacts(), ExistingOrganizationDep (+19 more)

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

### Community 60 - "test_auth_dependency.py"
Cohesion: 0.57
Nodes (6): assert_authentication_required(), TestClient, test_current_user_rejects_invalid_token(), test_current_user_rejects_unknown_user(), test_current_user_requires_bearer_token(), test_current_user_returns_authenticated_user()

### Community 61 - "get_current_user"
Cohesion: 0.24
Nodes (10): bearer_scheme, get_current_user(), SessionDep, Depends, HTTPAuthorizationCredentials, get_active_by_email(), get_active_by_id(), list_active() (+2 more)

### Community 63 - "routers/organizations.py"
Cohesion: 0.14
Nodes (16): UserNotFoundError, get_session(), AsyncSession, get_existing_document(), SessionDep, UUID, get_redis(), Redis (+8 more)

### Community 65 - "OrganizationMember"
Cohesion: 0.19
Nodes (22): LastOrganizationOwnerError, OrganizationPermissionDeniedError, is_idempotency_record_organization_key_unique_violation(), is_organization_member_primary_key_violation(), get_current_organization_member(), get_existing_organization_member(), CurrentUserDep, SessionDep (+14 more)

### Community 67 - "settings.py"
Cohesion: 0.05
Nodes (77): BaseSettings, claim_pending_for_processing(), get_by_id(), list_by_organization(), mark_completed(), mark_completed_as_failed(), mark_failed(), mark_stale_processing_as_failed() (+69 more)

### Community 68 - "services/conversations.py"
Cohesion: 0.16
Nodes (17): ContactNotFoundError, OrganizationNotFoundError, get_existing_contact(), SessionDep, UUID, get_existing_organization(), SessionDep, UUID (+9 more)

### Community 69 - "dependencies/conversations.py"
Cohesion: 0.23
Nodes (10): OrganizationPermission, get_existing_conversation(), ConversationFiltersQuery, CurrentUserDep, SessionDep, UUID, require_conversation_create_permission(), require_conversation_list_permission() (+2 more)

### Community 70 - "app_error_handler"
Cohesion: 0.20
Nodes (10): app_error_handler(), Request, JSONResponse, add_process_time_header(), health_check(), get, Request, Response (+2 more)

### Community 71 - "get_pagination"
Cohesion: 0.25
Nodes (8): Cookie, get_pagination(), PaginationParams, BaseModel, Response, ge, le, Query

## Knowledge Gaps
- **65 isolated node(s):** `crud`, `Project invariants`, `Graphify`, `Skills and MCP`, `Implementation workflow` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `DocumentStorage` (7× useful, score=6.509840575) _(code changed — re-verify)_
- `Document` (7× useful, score=6.444542326) _(code changed — re-verify)_
- `services/documents.py` (3× useful, score=2.875703015) _(code changed — re-verify)_
- `celery_app.py` (3× useful, score=2.806436942)
- `Organization` (3× useful, score=2.674743165)
- `User` (3× useful, score=2.674743165)
- `OutboxMessage` (2× useful, score=1.916375103)
- `settings.py` (2× useful, score=1.916017755) _(code changed — re-verify)_
- `Agent Instructions` (2× useful, score=1.890006971)
- `Implementation workflow` (2× useful, score=1.890006971)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_conversations.py`, `OrganizationMember`, `test_auth.py`, `services/conversations.py`, `services/users.py`, `services/auth.py`, `settings.py`, `exceptions.py`, `test_organizations.py`, `services/organizations.py`, `test_users.py`, `test_security.py`, `test_document_minio_integration.py`, `get_current_user`, `routers/organizations.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `Document` connect `User` to `evaluate_rag_baseline.py`, `settings.py`, `exceptions.py`, `routers/documents.py`, `test_document_minio_integration.py`, `test_document_api.py`, `routers/organizations.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `Organization` connect `User` to `OrganizationMember`, `settings.py`, `services/conversations.py`, `test_organizations.py`, `exceptions.py`, `services/organizations.py`, `test_document_minio_integration.py`, `services/contacts.py`, `routers/organizations.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `User` (e.g. with `Conversation` and `Document`) actually correct?**
  _`User` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Organization` (e.g. with `Contact` and `Conversation`) actually correct?**
  _`Organization` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Document` (e.g. with `DocumentChunk` and `DocumentStatus`) actually correct?**
  _`Document` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationRole` (e.g. with `OrganizationMember` and `OrganizationMemberListItem`) actually correct?**
  _`OrganizationRole` has 5 INFERRED edges - model-reasoned connections that need verification._