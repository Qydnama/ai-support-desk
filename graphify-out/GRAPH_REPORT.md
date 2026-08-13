# Graph Report - CRUD  (2026-08-12)

## Corpus Check
- 130 files · ~29,409 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 865 nodes · 2554 edges · 61 communities (59 shown, 2 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 141 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d8c7ecf6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Document
- Q: Как добавить настоящий upload pipeline Document после локального storage?
- User
- test_auth.py
- services/users.py
- dependencies/conversations.py
- settings.py
- test_organizations.py
- tasks/documents.py
- Organization
- test_spa_preflight_allows_authorization_header
- crud
- test_conversations.py
- Agent Instructions
- AI Support Desk — Project Context
- Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?
- Q: Прочитай файл rules6.md и проанализируй его и следуй его указаниям чтобы помоч мне сделать этот проект и научиться новым вещям
- Q: Как добавить минимальный контракт Document в текущие SQLAlchemy models без нарушения tenant architecture?
- exceptions.py
- OutboxMessage
- Q: Как безопасно подключить POST-загрузку документа к worker?
- test_users.py
- Q: Куда подключать загрузку документа в существующей архитектуре?
- get_pagination
- Q: Проверить миграцию create documents table
- FastAPI
- add_process_time_header
- routers/contacts.py
- Document-processing runbook
- get_current_user
- redis.py
- Q: Прочитай rules6.md, проанализируй его и следуй его указаниям, объясняя все новые вещи
- Q: Дальше: разобрать существующий Docker стенд перед добавлением MinIO
- Q: Продолжить: подготовить точное изменение Compose для MinIO и объяснить новые понятия
- Q: Дать полный код для перехода FastAPI и worker с local DocumentStorage на MinIO
- dependencies/users.py
- test_document_api.py

## God Nodes (most connected - your core abstractions)
1. `User` - 64 edges
2. `Organization` - 42 edges
3. `OrganizationRole` - 39 edges
4. `OrganizationMember` - 38 edges
5. `Document` - 33 edges
6. `AppError` - 31 edges
7. `Conversation` - 28 edges
8. `HttpErrorDetails` - 26 edges
9. `Base` - 24 edges
10. `create_user()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `test_document_task_marks_permanent_error_without_retry()` --indirect_call--> `mark_failed()`  [INFERRED]
  tests/test_document_task.py → repositories/documents.py
- `HttpErrorDetails` --uses--> `AuthenticationRequiredError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `HttpErrorDetails` --uses--> `OrganizationPermissionDeniedError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `Conversation` --uses--> `ConversationStatus`  [INFERRED]
  models/conversations.py → core/enums.py
- `OrganizationMember` --uses--> `OrganizationRole`  [INFERRED]
  models/organization_members.py → core/enums.py

## Import Cycles
- None detected.

## Communities (61 total, 2 thin omitted)

### Community 0 - "Document"
Cohesion: 0.06
Nodes (68): DocumentStatus, DocumentCreatePermissionDep, DocumentReadPermissionDep, DocumentUploadFile, ExistingDocumentDep, Document, parametrize, claim_pending_for_processing() (+60 more)

### Community 1 - "Q: Как добавить настоящий upload pipeline Document после локального storage?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как добавить настоящий upload pipeline Document после локального storage?, Source Nodes

### Community 2 - "User"
Cohesion: 0.07
Nodes (63): Connection, MessageSenderType, DeclarativeBase, get_existing_contact(), SessionDep, UUID, fixture, do_run_migrations() (+55 more)

### Community 3 - "test_auth.py"
Cohesion: 0.06
Nodes (87): Any, AuthenticationRequiredError, create_access_token(), create_refresh_token(), decode_access_token(), decode_refresh_token(), hash_password(), hash_refresh_token() (+79 more)

### Community 4 - "services/users.py"
Cohesion: 0.12
Nodes (30): CurrentUserAccountDep, is_user_email_unique_violation(), put, get_current_user(), CurrentUserDep, get, delete_user(), get_user() (+22 more)

### Community 5 - "dependencies/conversations.py"
Cohesion: 0.08
Nodes (46): ConversationCreatePermissionDep, ConversationListPermissionDep, ConversationReadPermissionDep, ConversationUpdatePermissionDep, ConversationStatus, OrganizationPermission, get_existing_conversation(), ConversationFiltersQuery (+38 more)

### Community 6 - "settings.py"
Cohesion: 0.23
Nodes (3): BaseSettings, Settings, test_document_task_marks_permanent_error_without_retry()

### Community 7 - "test_organizations.py"
Cohesion: 0.24
Nodes (36): OrganizationRole, create_stored_membership(), read_stored_membership(), authorization_headers(), create_organization(), create_user(), default_owner_headers(), delete_cached_value() (+28 more)

### Community 9 - "tasks/documents.py"
Cohesion: 0.33
Nodes (8): Task, DocumentProcessingTask, fail_stale_processing_documents(), OutboxPublisherTask, process_document(), publish_pending_outbox_messages(), Exception, test_stale_document_task_runs_maintenance_service()

### Community 10 - "Organization"
Cohesion: 0.06
Nodes (81): OrganizationPermissionDeniedError, is_idempotency_record_organization_key_unique_violation(), is_organization_member_primary_key_violation(), is_organization_slug_unique_violation(), get_current_organization_member(), get_existing_organization_member(), CurrentUserDep, SessionDep (+73 more)

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
Cohesion: 0.13
Nodes (35): app_error_handler(), HttpErrorDetails, Request, AppError, ContactEmailAlreadyExistsError, ContactNotFoundError, ConversationAlreadyAssignedError, ConversationMemberRequiredError (+27 more)

### Community 41 - "OutboxMessage"
Cohesion: 0.17
Nodes (23): OutboxMessage, list_pending_for_publish(), AsyncSession, publish_pending_messages(), TaskPublisher, test_outbox_publisher_task_runs_service(), configure_document_upload(), create_organization() (+15 more)

### Community 42 - "Q: Как безопасно подключить POST-загрузку документа к worker?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как безопасно подключить POST-загрузку документа к worker?, Source Nodes

### Community 43 - "test_users.py"
Cohesion: 0.25
Nodes (14): authorization_headers(), TestClient, UUID, register_user(), test_authenticated_user_id_validation(), test_health_check(), test_legacy_user_creation_is_disabled(), test_openapi_documents_redis_failure_responses() (+6 more)

### Community 45 - "Q: Куда подключать загрузку документа в существующей архитектуре?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Куда подключать загрузку документа в существующей архитектуре?, Source Nodes

### Community 46 - "get_pagination"
Cohesion: 0.25
Nodes (8): Cookie, get_pagination(), PaginationParams, BaseModel, Response, ge, le, Query

### Community 47 - "Q: Проверить миграцию create documents table"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Проверить миграцию create documents table, Source Nodes

### Community 48 - "FastAPI"
Cohesion: 0.27
Nodes (7): get_session(), AsyncSession, get_existing_document(), SessionDep, UUID, FastAPI, lifespan()

### Community 49 - "add_process_time_header"
Cohesion: 0.25
Nodes (8): JSONResponse, add_process_time_header(), health_check(), get, Request, Response, readiness_check(), middleware

### Community 50 - "routers/contacts.py"
Cohesion: 0.12
Nodes (27): ContactCreatePermissionDep, ContactReadPermissionDep, is_contact_email_unique_violation(), ExistingContactDep, create_contact(), get_contact(), list_contacts(), ExistingOrganizationDep (+19 more)

### Community 51 - "Document-processing runbook"
Cohesion: 0.18
Nodes (10): Check database migrations, Check retry behavior safely, Document-processing runbook, Full verification before a commit, Inspect logs, Open Flower, RabbitMQ queue dashboard, Start the project (+2 more)

### Community 52 - "get_current_user"
Cohesion: 0.40
Nodes (5): bearer_scheme, get_current_user(), SessionDep, Depends, HTTPAuthorizationCredentials

### Community 53 - "redis.py"
Cohesion: 0.50
Nodes (3): get_redis(), Redis, Request

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

### Community 60 - "dependencies/users.py"
Cohesion: 0.26
Nodes (10): get_current_user_account(), get_existing_user(), CurrentUserDep, SessionDep, UUID, get_active_by_email(), get_active_by_id(), list_active() (+2 more)

### Community 63 - "test_document_api.py"
Cohesion: 0.53
Nodes (8): create_organization(), create_stored_document(), async_sessionmaker, AsyncSession, TestClient, UUID, test_document_api_rejects_other_tenants_and_wrong_paths(), test_document_get_and_list_are_scoped_to_organization()

## Knowledge Gaps
- **52 isolated node(s):** `crud`, `Project invariants`, `Graphify`, `Skills and MCP`, `Implementation workflow` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `Document` (5× useful, score=4.730260081) _(code changed — re-verify)_
- `DocumentStorage` (4× useful, score=3.798494296) _(code changed — re-verify)_
- `Organization` (3× useful, score=2.795710534)
- `User` (3× useful, score=2.795710534)
- `celery_app.py` (2× useful, score=1.933343067)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `Document`, `test_conversations.py`, `test_auth.py`, `services/users.py`, `test_organizations.py`, `exceptions.py`, `Organization`, `test_users.py`, `FastAPI`, `get_current_user`, `dependencies/users.py`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `Organization` connect `Organization` to `Document`, `User`, `test_organizations.py`, `exceptions.py`, `routers/contacts.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Document` connect `Document` to `User`, `exceptions.py`, `Organization`, `FastAPI`, `test_document_api.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `User` (e.g. with `Conversation` and `Document`) actually correct?**
  _`User` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Organization` (e.g. with `Contact` and `Conversation`) actually correct?**
  _`Organization` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationRole` (e.g. with `OrganizationMember` and `OrganizationMemberListItem`) actually correct?**
  _`OrganizationRole` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationMember` (e.g. with `OrganizationRole` and `Base`) actually correct?**
  _`OrganizationMember` has 5 INFERRED edges - model-reasoned connections that need verification._