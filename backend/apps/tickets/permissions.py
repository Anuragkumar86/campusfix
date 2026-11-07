"""
Authorization rules for tickets. Everything here is evaluated on the server;
the frontend only mirrors the result (see ``ticket_permissions``).
"""
from django.db.models import Exists, OuterRef, Q
from rest_framework.permissions import BasePermission

from apps.accounts.models import Role

from .models import Assignment, Status, Ticket

# Roles a user can hold *with respect to one ticket*.
REPORTER, ASSIGNEE, MANAGER, ADMIN = "reporter", "assignee", "manager", "admin"

# (current, requested) -> rule. Anything not listed is an invalid transition.
TRANSITIONS = {
    (Status.OPEN, Status.ASSIGNED): {"via_assignment": True},
    (Status.ASSIGNED, Status.IN_PROGRESS): {"roles": {ASSIGNEE, ADMIN}},
    (Status.ASSIGNED, Status.OPEN): {"roles": {MANAGER, ADMIN}},
    (Status.IN_PROGRESS, Status.RESOLVED): {"roles": {ASSIGNEE, MANAGER, ADMIN}, "note_required": "A resolution note is required."},
    (Status.RESOLVED, Status.CLOSED): {"roles": {REPORTER, MANAGER, ADMIN}},
    (Status.RESOLVED, Status.REOPENED): {"roles": {REPORTER, MANAGER, ADMIN}, "note_required": "A reason is required to reopen a ticket."},
    (Status.CLOSED, Status.REOPENED): {"roles": {MANAGER, ADMIN}, "note_required": "A reason is required to reopen a ticket."},
    (Status.REOPENED, Status.ASSIGNED): {"via_assignment": True},
}


def visible_tickets_for(user):
    """Queryset of tickets the user may see (the single source of data scope)."""
    qs = Ticket.objects.all()
    if user.is_admin_role:
        return qs
    scope = Q(reporter=user)
    if user.role == Role.MAINTENANCE_STAFF:
        active = Assignment.objects.filter(ticket=OuterRef("pk"), assigned_to=user, is_active=True)
        scope |= Q(Exists(active))
    elif user.role == Role.DEPARTMENT_MANAGER and user.department_id:
        scope |= Q(department_id=user.department_id)
    return qs.filter(scope)


def roles_for(user, ticket) -> set:
    roles = set()
    if ticket.reporter_id == user.id:
        roles.add(REPORTER)
    if user.is_admin_role:
        roles.add(ADMIN)
    if user.role == Role.DEPARTMENT_MANAGER and user.department_id and user.department_id == ticket.department_id:
        roles.add(MANAGER)
    assignment = ticket.current_assignment
    if assignment and assignment.assigned_to_id == user.id:
        roles.add(ASSIGNEE)
    return roles


def can_view(user, ticket) -> bool:
    return bool(roles_for(user, ticket))


def can_comment(user, ticket) -> bool:
    return user.has_perm("tickets.add_comment") and bool(roles_for(user, ticket))


def can_attach(user, ticket) -> bool:
    return user.has_perm("tickets.add_attachment") and bool(roles_for(user, ticket)) and ticket.status != Status.CLOSED


def can_manage(user, ticket) -> bool:
    return bool(roles_for(user, ticket) & {MANAGER, ADMIN})


def can_assign(user, ticket) -> bool:
    return user.has_perm("tickets.add_assignment") and can_manage(user, ticket)


def can_edit_basic_fields(user, ticket) -> bool:
    roles = roles_for(user, ticket)
    if roles & {MANAGER, ADMIN}:
        return True
    return REPORTER in roles and ticket.status == Status.OPEN


def allowed_transitions(user, ticket) -> list:
    """Statuses this user may request through the status endpoint right now."""
    roles = roles_for(user, ticket)
    result = []
    for (current, requested), rule in TRANSITIONS.items():
        if current == ticket.status and not rule.get("via_assignment") and roles & rule["roles"]:
            result.append(requested)
    return result


def ticket_permissions(user, ticket) -> dict:
    return {
        "can_comment": can_comment(user, ticket),
        "can_attach": can_attach(user, ticket),
        "can_assign": can_assign(user, ticket) and ticket.status not in (Status.RESOLVED, Status.CLOSED),
        "can_set_priority": can_manage(user, ticket) and ticket.status not in (Status.RESOLVED, Status.CLOSED),
        "can_edit": can_edit_basic_fields(user, ticket),
        "available_transitions": allowed_transitions(user, ticket),
    }


class CanCreateTicket(BasePermission):
    """Students (and administrators for support/testing) with the add_ticket permission."""

    message = "You do not have permission to report issues."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and user.role in (Role.STUDENT, Role.ADMINISTRATOR)
            and user.has_perm("tickets.add_ticket")
        )
