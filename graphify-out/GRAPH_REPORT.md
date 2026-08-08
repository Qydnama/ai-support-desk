# Graph Report - CRUD  (2026-08-08)

## Corpus Check
- 92 files · ~20,819 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 621 nodes · 1929 edges · 33 communities (31 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 97 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `75036990`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- conftest.py
- test_auth.py
- services/users.py
- OrganizationMember
- routers/contacts.py
- test_organizations.py
- User
- routers/organizations.py
- test_spa_preflight_allows_authorization_header
- crud
- Agent Instructions
- AI Support Desk — Project Context
- Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?

## God Nodes (most connected - your core abstractions)
1. `User` - 51 edges
2. `OrganizationRole` - 39 edges
3. `OrganizationMember` - 38 edges
4. `Organization` - 29 edges
5. `Conversation` - 28 edges
6. `AppError` - 25 edges
7. `create_user()` - 23 edges
8. `create_stored_membership()` - 22 edges
9. `authorization_headers()` - 22 edges
10. `create_organization()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `OrganizationMember` --uses--> `OrganizationRole`  [INFERRED]
  models/organization_members.py → core/enums.py
- `OrganizationMemberListItem` --uses--> `OrganizationRole`  [INFERRED]
  schemas/organization_members.py → core/enums.py
- `OrganizationMemberRead` --uses--> `OrganizationRole`  [INFERRED]
  schemas/organization_members.py → core/enums.py
- `OrganizationMemberRoleUpdate` --uses--> `OrganizationRole`  [INFERRED]
  schemas/organization_members.py → core/enums.py
- `IssuedTokens` --uses--> `UserEmailAlreadyExistsError`  [INFERRED]
  services/auth.py → core/exceptions.py

## Import Cycles
- None detected.

## Communities (33 total, 2 thin omitted)

### Community 2 - "conftest.py"
Cohesion: 0.05
Nodes (95): Connection, ConversationCreatePermissionDep, ConversationListPermissionDep, ConversationReadPermissionDep, ConversationUpdatePermissionDep, ConversationStatus, MessageSenderType, DeclarativeBase (+87 more)

### Community 3 - "test_auth.py"
Cohesion: 0.05
Nodes (90): Any, BaseSettings, create_access_token(), create_refresh_token(), decode_access_token(), decode_refresh_token(), hash_password(), hash_refresh_token() (+82 more)

### Community 4 - "services/users.py"
Cohesion: 0.12
Nodes (29): CurrentUserAccountDep, put, get_current_user(), CurrentUserDep, get, delete_user(), get_user(), list_users() (+21 more)

### Community 5 - "OrganizationMember"
Cohesion: 0.06
Nodes (71): app_error_handler(), HttpErrorDetails, Request, OrganizationPermission, AppError, AuthenticationRequiredError, ContactEmailAlreadyExistsError, ContactNotFoundError (+63 more)

### Community 6 - "routers/contacts.py"
Cohesion: 0.08
Nodes (39): ContactCreatePermissionDep, ContactReadPermissionDep, Cookie, is_contact_email_unique_violation(), is_idempotency_record_organization_key_unique_violation(), is_organization_member_primary_key_violation(), is_user_email_unique_violation(), get_pagination() (+31 more)

### Community 7 - "test_organizations.py"
Cohesion: 0.15
Nodes (64): OrganizationRole, MonkeyPatch, create_stored_membership(), read_stored_membership(), authorization_headers(), create_contact(), create_conversation(), create_organization() (+56 more)

### Community 9 - "User"
Cohesion: 0.13
Nodes (27): bearer_scheme, get_current_user(), SessionDep, get_existing_user(), SessionDep, Depends, HTTPAuthorizationCredentials, User (+19 more)

### Community 10 - "routers/organizations.py"
Cohesion: 0.07
Nodes (56): is_organization_slug_unique_violation(), ExistingOrganizationMemberDep, ExistingUserDep, MemberCreatePermissionDep, MemberDeletePermissionDep, MemberReadPermissionDep, MemberRoleUpdatePermissionDep, OrganizationDeletePermissionDep (+48 more)

### Community 33 - "Agent Instructions"
Cohesion: 0.25
Nodes (7): Agent Instructions, Graphify, Implementation workflow, Project invariants, Repository hygiene, Skills and MCP, Tool routing

### Community 35 - "AI Support Desk — Project Context"
Cohesion: 0.33
Nodes (5): Agent guidance, AI Support Desk — Project Context, Architecture, Commands, Current Redis implementation

### Community 36 - "Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Как правильно совместить ExistingOrganizationDep и cache-aside без повторного SELECT организации?, Source Nodes

## Knowledge Gaps
- **13 isolated node(s):** `crud`, `Project invariants`, `Graphify`, `Skills and MCP`, `Implementation workflow` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `conftest.py`, `test_auth.py`, `services/users.py`, `OrganizationMember`, `test_organizations.py`, `routers/organizations.py`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Why does `OrganizationMember` connect `OrganizationMember` to `User`, `conftest.py`, `routers/organizations.py`, `test_organizations.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `OrganizationRole` connect `test_organizations.py` to `conftest.py`, `routers/organizations.py`, `OrganizationMember`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `User` (e.g. with `Conversation` and `Message`) actually correct?**
  _`User` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationRole` (e.g. with `OrganizationMember` and `OrganizationMemberListItem`) actually correct?**
  _`OrganizationRole` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrganizationMember` (e.g. with `OrganizationRole` and `Base`) actually correct?**
  _`OrganizationMember` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Organization` (e.g. with `Contact` and `Conversation`) actually correct?**
  _`Organization` has 5 INFERRED edges - model-reasoned connections that need verification._