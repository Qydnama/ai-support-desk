from core.enums import OrganizationPermission, OrganizationRole
from core.permissions import ROLE_PERMISSIONS


def test_agent_permissions() -> None:
    permissions = ROLE_PERMISSIONS[OrganizationRole.AGENT]

    assert OrganizationPermission.CONTACT_CREATE in permissions
    assert OrganizationPermission.MESSAGE_CREATE in permissions
    assert OrganizationPermission.MEMBER_CREATE not in permissions
    assert OrganizationPermission.ORGANIZATION_DELETE not in permissions


def test_admin_permissions_include_agent_management() -> None:
    permissions = ROLE_PERMISSIONS[OrganizationRole.ADMIN]

    assert OrganizationPermission.MEMBER_CREATE in permissions
    assert OrganizationPermission.MEMBER_DELETE in permissions
    assert OrganizationPermission.ORGANIZATION_UPDATE in permissions
    assert OrganizationPermission.MEMBER_ROLE_UPDATE not in permissions
    assert OrganizationPermission.ORGANIZATION_DELETE not in permissions


def test_owner_has_every_organization_permission() -> None:
    assert ROLE_PERMISSIONS[OrganizationRole.OWNER] == frozenset(
        OrganizationPermission,
    )
