"""
Account-management service: the single place that keeps ``User.role`` and the
Django Group membership consistent, and defines the group permission sets.
"""
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied

from .models import Role

# role -> Django Group name (also the names listed in the requirements)
ROLE_GROUPS = {
    Role.STUDENT: "STUDENT",
    Role.MAINTENANCE_STAFF: "MAINTENANCE_STAFF",
    Role.DEPARTMENT_MANAGER: "DEPARTMENT_MANAGER",
    Role.ADMINISTRATOR: "ADMINISTRATOR",
}

# Model permissions per group ("app_label.codename").
_COMMENT_ATTACH = [
    "tickets.view_ticket",
    "tickets.view_comment",
    "tickets.add_comment",
    "tickets.view_attachment",
    "tickets.add_attachment",
    "tickets.view_tickethistory",
]
GROUP_PERMISSIONS = {
    "STUDENT": _COMMENT_ATTACH + ["tickets.add_ticket", "departments.view_category", "departments.view_department"],
    "MAINTENANCE_STAFF": _COMMENT_ATTACH + ["tickets.change_ticket"],
    "DEPARTMENT_MANAGER": _COMMENT_ATTACH
    + [
        "tickets.change_ticket",
        "tickets.view_assignment",
        "tickets.add_assignment",
        "tickets.change_assignment",
        "departments.view_category",
        "departments.view_department",
        "accounts.view_user",
    ],
}
# ADMINISTRATOR receives every permission of the project's own apps (see below).
ADMIN_APP_LABELS = ("accounts", "departments", "tickets")


def ensure_role_groups() -> None:
    """Create the four role groups and (re)assign their permissions. Repeatable."""
    for role, group_name in ROLE_GROUPS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        if role == Role.ADMINISTRATOR:
            perms = Permission.objects.filter(content_type__app_label__in=ADMIN_APP_LABELS)
            perms = perms | Permission.objects.filter(content_type__app_label="auth", content_type__model__in=["group", "permission"])
        else:
            perms = Permission.objects.none()
            for dotted in GROUP_PERMISSIONS[group_name]:
                app_label, codename = dotted.split(".")
                perms = perms | Permission.objects.filter(content_type__app_label=app_label, codename=codename)
        group.permissions.set(perms)


def ensure_role_groups_after_migrate(sender=None, using="default", **kwargs):
    """post_migrate hook: make sure permissions exist, then build the groups."""
    from django.apps import apps as global_apps
    from django.contrib.auth.management import create_permissions

    for app_config in global_apps.get_app_configs():
        if app_config.models_module is not None:
            create_permissions(app_config, verbosity=0, using=using)
    ensure_role_groups()


def sync_user_group(user) -> None:
    """Put the user in exactly the role group that matches ``user.role``."""
    wanted_name = ROLE_GROUPS[user.role]
    wanted, _ = Group.objects.get_or_create(name=wanted_name)
    role_group_names = set(ROLE_GROUPS.values())
    current = set(user.groups.filter(name__in=role_group_names).values_list("name", flat=True))
    stale = current - {wanted_name}
    if stale:
        user.groups.remove(*Group.objects.filter(name__in=stale))
    if wanted_name not in current:
        user.groups.add(wanted)


def change_user_role(*, actor, target, role, department=None):
    """
    Change another user's role/department. Users can never edit their own role,
    and only administrators may change anyone's.
    """
    if not actor.is_authenticated or not actor.is_admin_role:
        raise PermissionDenied("Only administrators can change roles.")
    if actor.pk == target.pk:
        raise PermissionDenied("You cannot change your own role.")
    if role not in Role.values:
        raise ValueError(f"Unknown role: {role}")
    target.role = role
    target.department = department
    target.full_clean(exclude=["password"])
    target.save()  # save() also synchronises the Django Group
    return target
