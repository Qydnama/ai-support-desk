# Graph Report - CRUD  (2026-08-11)

## Corpus Check
- 123 files · ~27,369 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 810 nodes · 2409 edges · 53 communities (51 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 121 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9b4402f7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- upload_document
- Q: Как добавить настоящий upload pipeline Document после локального storage?
- User
- test_auth.py
- services/users.py
- routers/conversations.py
- test_document_processing.py
- test_organizations.py
- repositories/users.py
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
- settings.py
- Q: Как безопасно подключить POST-загрузку документа к worker?
- test_users.py
- Q: Куда подключать загрузку документа в существующей архитектуре?
- get_pagination
- Q: Проверить миграцию create documents table
- test_document_api.py
- OrganizationMember
- create_contact
- Document-processing runbook
- test_contacts.py

## God Nodes (most connected - your core abstractions)
1. `User` - 62 edges
2. `Organization` - 40 edges
3. `OrganizationRole` - 39 edges
4. `OrganizationMember` - 38 edges
5. `AppError` - 30 edges
6. `Document` - 29 edges
7. `Conversation` - 28 edges
8. `HttpErrorDetails` - 25 edges
9. `Base` - 24 edges
10. `create_user()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `test_document_task_marks_permanent_error_without_retry()` --indirect_call--> `mark_failed()`  [INFERRED]
  tests/test_document_task.py → repositories/documents.py
- `HttpErrorDetails` --uses--> `LoginRateLimitExceededError`  [INFERRED]
  api/exception_handlers.py → core/exceptions.py
- `Conversation` --uses--> `ConversationStatus`  [INFERRED]
  models/conversations.py → core/enums.py
- `DocumentRead` --uses--> `DocumentStatus`  [INFERRED]
  schemas/documents.py → core/enums.py
- `DisposableTestEngine` --uses--> `DocumentStatus`  [INFERRED]
  tests/test_document_processing.py → core/enums.py

## Import Cycles
- None detected.

## Communities (53 total, 2 thin omitted)

### Community 0 - "upload_document"
Cohesion: 0.16
Nodes (16): DocumentCreatePermissionDep, DocumentReadPermissionDep, DocumentUploadFile, ExistingDocumentDep, get_document(), list_documents(), CurrentUserDep, ExistingOrganizationDep (+8 more)

### Community 1 - "Q: Как добавить настоящий upload pipeline Document после локального storage?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как добавить настоящий upload pipeline Document после локального storage?, Source Nodes

### Community 2 - "User"
Cohesion: 0.07
Nodes (70): Connection, DocumentStatus, MessageSenderType, is_contact_email_unique_violation(), is_idempotency_record_organization_key_unique_violation(), is_organization_member_primary_key_violation(), DeclarativeBase, fixture (+62 more)

### Community 3 - "test_auth.py"
Cohesion: 0.05
Nodes (86): Any, LoginRateLimitExceededError, create_access_token(), create_refresh_token(), decode_access_token(), decode_refresh_token(), hash_password(), hash_refresh_token() (+78 more)

### Community 4 - "services/users.py"
Cohesion: 0.28
Nodes (13): is_user_email_unique_violation(), BaseModel, field_validator, UserBase, UserCreate, UserReplace, UserUpdate, _commit() (+5 more)

### Community 5 - "routers/conversations.py"
Cohesion: 0.10
Nodes (41): ConversationCreatePermissionDep, ConversationListPermissionDep, ConversationReadPermissionDep, ConversationUpdatePermissionDep, ConversationStatus, ExistingConversationDep, IdempotencyKeyHeader, MessageCreatePermissionDep (+33 more)

### Community 6 - "test_document_processing.py"
Cohesion: 0.11
Nodes (32): parametrize, claim_pending_for_processing(), get_by_id(), list_by_organization(), mark_completed(), mark_failed(), mark_stale_processing_as_failed(), AsyncSession (+24 more)

### Community 7 - "test_organizations.py"
Cohesion: 0.24
Nodes (36): OrganizationRole, create_stored_membership(), read_stored_membership(), authorization_headers(), create_organization(), create_user(), default_owner_headers(), delete_cached_value() (+28 more)

### Community 9 - "repositories/users.py"
Cohesion: 0.53
Nodes (5): get_active_by_email(), get_active_by_id(), list_active(), AsyncSession, UUID

### Community 10 - "services/organizations.py"
Cohesion: 0.07
Nodes (56): is_organization_slug_unique_violation(), ExistingOrganizationMemberDep, ExistingUserDep, MemberCreatePermissionDep, MemberDeletePermissionDep, MemberReadPermissionDep, MemberRoleUpdatePermissionDep, OrganizationDeletePermissionDep (+48 more)

### Community 32 - "test_conversations.py"
Cohesion: 0.36
Nodes (28): MonkeyPatch, authorization_headers(), create_contact(), create_conversation(), create_organization(), create_user(), async_sessionmaker, AsyncSession (+20 more)

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
Cohesion: 0.05
Nodes (85): app_error_handler(), HttpErrorDetails, Request, bearer_scheme, AppError, AuthenticationRequiredError, ContactEmailAlreadyExistsError, ContactNotFoundError (+77 more)

### Community 41 - "settings.py"
Cohesion: 0.09
Nodes (34): BaseSettings, OutboxMessage, list_pending_for_publish(), AsyncSession, publish_pending_messages(), Settings, Task, TaskPublisher (+26 more)

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

### Community 48 - "test_document_api.py"
Cohesion: 0.53
Nodes (8): create_organization(), create_stored_document(), async_sessionmaker, AsyncSession, TestClient, UUID, test_document_api_rejects_other_tenants_and_wrong_paths(), test_document_get_and_list_are_scoped_to_organization()

### Community 49 - "OrganizationMember"
Cohesion: 0.16
Nodes (21): OrganizationPermission, get_existing_conversation(), ConversationFiltersQuery, CurrentUserDep, SessionDep, UUID, require_conversation_create_permission(), require_conversation_list_permission() (+13 more)

### Community 50 - "create_contact"
Cohesion: 0.19
Nodes (14): ContactCreatePermissionDep, ContactReadPermissionDep, ExistingContactDep, create_contact(), get_contact(), list_contacts(), ExistingOrganizationDep, get (+6 more)

### Community 51 - "Document-processing runbook"
Cohesion: 0.18
Nodes (10): Check database migrations, Check retry behavior safely, Document-processing runbook, Full verification before a commit, Inspect logs, Open Flower, RabbitMQ queue dashboard, Start the project (+2 more)

### Community 52 - "test_contacts.py"
Cohesion: 0.42
Nodes (9): create_organization(), async_sessionmaker, AsyncSession, TestClient, test_contact_create_get_and_list(), test_contact_email_is_unique_inside_organization(), test_contact_not_found(), test_contacts_require_tenant_membership() (+1 more)

## Knowledge Gaps
- **40 isolated node(s):** `crud`, `Project invariants`, `Graphify`, `Skills and MCP`, `Implementation workflow` (+35 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `Document` (4× useful, score=3.828186092)
- `DocumentStorage` (3× useful, score=2.871970836)
- `Organization` (3× useful, score=2.869069791)
- `User` (3× useful, score=2.869069791)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_conversations.py`, `test_auth.py`, `services/users.py`, `routers/conversations.py`, `test_document_processing.py`, `test_organizations.py`, `exceptions.py`, `repositories/users.py`, `services/organizations.py`, `test_users.py`, `OrganizationMember`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Why does `Organization` connect `User` to `test_document_processing.py`, `test_organizations.py`, `exceptions.py`, `services/organizations.py`, `OrganizationMember`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `Document` connect `User` to `exceptions.py`, `test_document_api.py`, `test_document_processing.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `User` (e.g. with `Conversation` and `Document`) actually correct?**
  _`User` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Organization` (e.g. with `Contact` and `Conversation`) actually correct?**
  _`Organization` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationRole` (e.g. with `OrganizationMember` and `OrganizationMemberListItem`) actually correct?**
  _`OrganizationRole` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationMember` (e.g. with `OrganizationRole` and `Base`) actually correct?**
  _`OrganizationMember` has 5 INFERRED edges - model-reasoned connections that need verification._