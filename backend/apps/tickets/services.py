"""
Ticket business rules. Every state-changing operation runs inside one database
transaction, locks the ticket row (select_for_update) and writes its history
record in that same transaction, so history exists only if the change succeeded.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status as http
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.accounts.models import Role, User

from . import permissions as perms
from .models import Assignment, Attachment, Comment, Status, Ticket, TicketHistory
from .validators import validate_image_upload

logger = logging.getLogger(__name__)
Event = TicketHistory.Event


class Conflict(APIException):
    status_code = http.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state of the ticket."
    default_code = "conflict"


# ----------------------------------------------------------------- helpers
def record_history(ticket, actor, event_type, old=None, new=None, note=""):
    return TicketHistory.objects.create(
        ticket=ticket,
        changed_by=actor,
        event_type=event_type,
        old_value=None if old is None else str(old),
        new_value=None if new is None else str(new),
        note=note or "",
    )


def sla_due_dates(priority, start):
    target = settings.SLA_TARGETS[priority]
    return start + timedelta(hours=target["response_hours"]), start + timedelta(hours=target["resolution_hours"])


def _lock(ticket_id) -> Ticket:
    return Ticket.objects.select_for_update().select_related("category", "department", "reporter").get(pk=ticket_id)


def _mark_first_response(ticket, actor):
    """The first action by someone other than the reporter counts as the response."""
    if ticket.first_response_at is None and actor.id != ticket.reporter_id:
        ticket.first_response_at = timezone.now()


# ------------------------------------------------------------------ create
@transaction.atomic
def create_ticket(*, reporter, category, title, description, building, floor="", room_or_area="", image=None):
    if not category.is_active or not category.department.is_active:
        raise ValidationError({"category": "This category is not available."})
    now = timezone.now()
    response_due, resolution_due = sla_due_dates("MEDIUM", now)
    ticket = Ticket.objects.create(
        reporter=reporter,  # always the authenticated user, never client-supplied
        category=category,
        department=category.department,  # derived from the category mapping
        title=title,
        description=description,
        building=building,
        floor=floor,
        room_or_area=room_or_area,
        status=Status.OPEN,
        priority="MEDIUM",
        sla_started_at=now,
        response_due_at=response_due,
        resolution_due_at=resolution_due,
    )
    record_history(ticket, reporter, Event.CREATED, None, Status.OPEN, "Ticket submitted.")
    if image is not None:
        _store_attachment(ticket, reporter, image, record=False)
    return ticket


# -------------------------------------------------------------- attachments
def _store_attachment(ticket, actor, upload, record=True):
    content_type, ext, safe_name = validate_image_upload(upload)
    attachment = Attachment(
        ticket=ticket,
        uploaded_by=actor,
        original_filename=safe_name,
        content_type=content_type,
        file_size=upload.size,
    )
    attachment._stored_ext = ext
    attachment.file.save(safe_name, upload, save=False)
    try:
        attachment.save()
    except Exception:
        attachment.file.delete(save=False)  # do not leave an orphan file behind
        raise
    if record:
        record_history(ticket, actor, Event.ATTACHMENT, None, safe_name)
    return attachment


@transaction.atomic
def add_attachment(*, ticket_id, actor, upload):
    ticket = _lock(ticket_id)
    if not perms.can_attach(actor, ticket):
        raise PermissionDenied("You cannot add attachments to this ticket.")
    return _store_attachment(ticket, actor, upload)


# ---------------------------------------------------------------- comments
@transaction.atomic
def add_comment(*, ticket_id, actor, message):
    message = (message or "").strip()
    if not message:
        raise ValidationError({"message": "Comment cannot be empty."})
    if len(message) > 2000:
        raise ValidationError({"message": "Comment is too long (maximum 2000 characters)."})
    ticket = _lock(ticket_id)
    if not perms.can_comment(actor, ticket):
        raise PermissionDenied("You cannot comment on this ticket.")
    comment = Comment.objects.create(ticket=ticket, author=actor, message=message)
    _mark_first_response(ticket, actor)
    ticket.save(update_fields=["first_response_at", "updated_at"])
    return comment


# -------------------------------------------------------------- assignment
@transaction.atomic
def assign_ticket(*, ticket_id, actor, assignee_id, note=""):
    ticket = _lock(ticket_id)
    if not perms.can_assign(actor, ticket):
        raise PermissionDenied("You cannot assign this ticket.")
    if ticket.status in (Status.RESOLVED, Status.CLOSED):
        raise Conflict("A resolved or closed ticket cannot be assigned. Reopen it first.")
    try:
        assignee = User.objects.get(pk=assignee_id)
    except (User.DoesNotExist, ValueError, TypeError):
        raise ValidationError({"assigned_to": "Selected staff member does not exist."})
    if (
        assignee.role != Role.MAINTENANCE_STAFF
        or not assignee.is_active
        or assignee.department_id != ticket.department_id
    ):
        raise ValidationError({"assigned_to": "Staff member must be an active maintenance staff user in the ticket's department."})

    previous = ticket.assignments.select_for_update().filter(is_active=True).select_related("assigned_to").first()
    if previous and previous.assigned_to_id == assignee.id:
        raise Conflict("This staff member is already assigned to the ticket.")
    now = timezone.now()
    if previous:
        previous.is_active = False
        previous.unassigned_at = now
        previous.save(update_fields=["is_active", "unassigned_at"])  # old record is preserved
    Assignment.objects.create(ticket=ticket, assigned_to=assignee, assigned_by=actor, assignment_note=note.strip(), assigned_at=now)
    record_history(
        ticket, actor, Event.ASSIGNMENT,
        previous.assigned_to.display_name if previous else None,
        assignee.display_name, note.strip(),
    )
    old_status = ticket.status
    if old_status != Status.ASSIGNED:
        ticket.status = Status.ASSIGNED
        record_history(ticket, actor, Event.STATUS, old_status, Status.ASSIGNED)
    _mark_first_response(ticket, actor)
    ticket.save()
    return ticket


# ------------------------------------------------------------------ status
@transaction.atomic
def change_status(*, ticket_id, actor, new_status, note=""):
    ticket = _lock(ticket_id)
    note = (note or "").strip()
    if new_status not in Status.values:
        raise ValidationError({"status": "Unknown status."})
    rule = perms.TRANSITIONS.get((ticket.status, new_status))
    if rule is None:
        raise Conflict(f"A ticket cannot move from {ticket.status} to {new_status}.")
    if rule.get("via_assignment"):
        raise Conflict("Use the assignment endpoint to assign this ticket.")
    if not (perms.roles_for(actor, ticket) & rule["roles"]):
        raise PermissionDenied("You are not allowed to make this status change.")
    if rule.get("note_required") and not note:
        raise ValidationError({"note": rule["note_required"]})

    old_status = ticket.status
    now = timezone.now()
    if old_status == Status.ASSIGNED and new_status == Status.OPEN:
        # Assignment removed with no replacement: close the active assignment.
        ticket.assignments.filter(is_active=True).update(is_active=False, unassigned_at=now)
        record_history(ticket, actor, Event.ASSIGNMENT, "assigned", None, note)
    ticket.status = new_status
    if new_status == Status.RESOLVED:
        ticket.resolved_at = now
        ticket.resolution_note = note
    elif new_status == Status.CLOSED:
        ticket.closed_at = now
    elif new_status == Status.REOPENED:
        ticket.resolved_at = None
        ticket.closed_at = None
        ticket.first_response_at = None
        # restart the SLA clock for the reopened work
        ticket.sla_started_at = now
        old_due = ticket.resolution_due_at
        ticket.response_due_at, ticket.resolution_due_at = sla_due_dates(ticket.priority, now)
        record_history(ticket, actor, Event.DEADLINE, old_due.isoformat() if old_due else None, ticket.resolution_due_at.isoformat(), "SLA restarted after reopening.")
    record_history(ticket, actor, Event.STATUS, old_status, new_status, note)
    _mark_first_response(ticket, actor)
    ticket.save()
    return ticket


# ---------------------------------------------------------------- priority
@transaction.atomic
def change_priority(*, ticket_id, actor, priority, note=""):
    ticket = _lock(ticket_id)
    if not perms.can_manage(actor, ticket):
        raise PermissionDenied("You cannot change the priority of this ticket.")
    if priority not in settings.SLA_TARGETS:
        raise ValidationError({"priority": "Unknown priority."})
    if ticket.status in (Status.RESOLVED, Status.CLOSED):
        raise Conflict("Priority cannot be changed on a resolved or closed ticket.")
    if priority == ticket.priority:
        raise Conflict("The ticket already has this priority.")
    old_priority = ticket.priority
    old_response, old_resolution = ticket.response_due_at, ticket.resolution_due_at
    ticket.priority = priority
    ticket.response_due_at, ticket.resolution_due_at = sla_due_dates(priority, ticket.sla_started_at)
    record_history(ticket, actor, Event.PRIORITY, old_priority, priority, (note or "").strip())
    record_history(
        ticket, actor, Event.DEADLINE,
        old_resolution.isoformat() if old_resolution else None,
        ticket.resolution_due_at.isoformat(), "Deadlines recalculated for the new priority.",
    )
    ticket.save()
    return ticket
