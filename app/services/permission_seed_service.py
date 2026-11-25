from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


PERMISSION_NAMES = (
    "employee:create",
    "employee:read",
    "employee:update",
    "employee:delete",
    "skill:create",
    "skill:read",
    "skill:update",
    "skill:delete",
    "project:create",
    "project:read",
    "project:update",
    "project:delete",
    "allocation:create",
    "allocation:read",
    "allocation:update",
    "allocation:cancel",
    "project_skill:manage",
    "project_skill:read",
    "role:assign",
    "role:read",
)

ROLE_PERMISSION_NAMES = {
    "Admin": frozenset(PERMISSION_NAMES),
    "Manager": frozenset(
        {
            "employee:read",
            "skill:read",
            "project:create",
            "project:read",
            "project:update",
            "allocation:create",
            "allocation:read",
            "allocation:update",
            "allocation:cancel",
            "project_skill:manage",
            "project_skill:read",
        }
    ),
    "Employee": frozenset(
        {
            "employee:read",
            "employee:update",
            "skill:read",
            "project:read",
            "allocation:read",
            "project_skill:read",
        }
    ),
}


def seed_permission_catalogue(db: Session) -> tuple[int, int]:
    role_names = tuple(ROLE_PERMISSION_NAMES)
    roles = db.scalars(
        select(Role).where(Role.role_name.in_(role_names))
    ).all()
    roles_by_name = {role.role_name: role for role in roles}

    missing_roles = sorted(set(role_names) - set(roles_by_name))
    if missing_roles:
        raise ValueError(
            "Required roles are missing; no roles were created: "
            + ", ".join(missing_roles)
        )

    role_ids = [roles_by_name[name].role_id for name in role_names]
    existing_catalogue_grants = db.execute(
        select(Role.role_name, Permission.name)
        .join(RolePermission, RolePermission.role_id == Role.role_id)
        .join(
            Permission,
            Permission.permission_id == RolePermission.permission_id,
        )
        .where(
            Role.role_id.in_(role_ids),
            Permission.name.in_(PERMISSION_NAMES),
        )
    ).all()

    unexpected_grants = sorted(
        (role_name, permission_name)
        for role_name, permission_name in existing_catalogue_grants
        if permission_name not in ROLE_PERMISSION_NAMES[role_name]
    )
    if unexpected_grants:
        formatted_grants = ", ".join(
            f"{role_name} -> {permission_name}"
            for role_name, permission_name in unexpected_grants
        )
        raise ValueError(
            "Unexpected catalogue role-permission associations exist; "
            "no data was changed: "
            + formatted_grants
        )

    permissions = db.scalars(
        select(Permission).where(Permission.name.in_(PERMISSION_NAMES))
    ).all()
    permissions_by_name = {
        permission.name: permission for permission in permissions
    }

    created_permissions = 0
    for permission_name in PERMISSION_NAMES:
        if permission_name not in permissions_by_name:
            permission = Permission(name=permission_name)
            db.add(permission)
            permissions_by_name[permission_name] = permission
            created_permissions += 1

    db.flush()

    existing_assignments = {
        (role_id, permission_id)
        for role_id, permission_id in db.execute(
            select(RolePermission.role_id, RolePermission.permission_id)
            .where(RolePermission.role_id.in_(role_ids))
        ).all()
    }

    created_assignments = 0
    for role_name, desired_permissions in ROLE_PERMISSION_NAMES.items():
        role_id = roles_by_name[role_name].role_id
        for permission_name in sorted(desired_permissions):
            permission_id = permissions_by_name[permission_name].permission_id
            assignment = (role_id, permission_id)
            if assignment not in existing_assignments:
                db.add(
                    RolePermission(
                        role_id=role_id,
                        permission_id=permission_id,
                    )
                )
                existing_assignments.add(assignment)
                created_assignments += 1

    db.flush()
    return created_permissions, created_assignments
