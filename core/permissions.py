from core.enums import (
    OrganizationPermission,
    OrganizationRole,
)

AGENT_PERMISSIONS = frozenset({
    OrganizationPermission.ORGANIZATION_READ,
    OrganizationPermission.MEMBER_READ,
    OrganizationPermission.CONTACT_READ,
    OrganizationPermission.CONTACT_CREATE,
    OrganizationPermission.CONVERSATION_READ,
    OrganizationPermission.CONVERSATION_CREATE,
    OrganizationPermission.CONVERSATION_UPDATE,
    OrganizationPermission.MESSAGE_READ,
    OrganizationPermission.MESSAGE_CREATE,
})


ADMIN_PERMISSIONS = AGENT_PERMISSIONS | frozenset({
    OrganizationPermission.ORGANIZATION_UPDATE,
    OrganizationPermission.MEMBER_CREATE,
    OrganizationPermission.MEMBER_DELETE,
})


OWNER_PERMISSIONS = ADMIN_PERMISSIONS | frozenset({
    OrganizationPermission.ORGANIZATION_DELETE,
    OrganizationPermission.MEMBER_ROLE_UPDATE,
})


ROLE_PERMISSIONS: dict[
    OrganizationRole,
    frozenset[OrganizationPermission],
] = {
    OrganizationRole.AGENT: AGENT_PERMISSIONS,
    OrganizationRole.ADMIN: ADMIN_PERMISSIONS,
    OrganizationRole.OWNER: OWNER_PERMISSIONS,
}