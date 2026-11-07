import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Status(models.TextChoices):
    OPEN = "OPEN", "Open"
    ASSIGNED = "ASSIGNED", "Assigned"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    RESOLVED = "RESOLVED", "Resolved"
    REOPENED = "REOPENED", "Reopened"
    CLOSED = "CLOSED", "Closed"


class Priority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


TERMINAL_STATUSES = (Status.RESOLVED, Status.CLOSED)
ACTIVE_STATUSES = (Status.OPEN, Status.ASSIGNED, Status.IN_PROGRESS, Status.REOPENED)


class TicketQuerySet(models.QuerySet):
    def overdue(self):
        """Active tickets whose resolution deadline passed, or whose response
        deadline passed without a first response."""
        now = timezone.now()
        return self.exclude(status__in=TERMINAL_STATUSES).filter(
            Q(resolution_due_at__lt=now) | Q(first_response_at__isnull=True, response_due_at__lt=now)
        )


class Ticket(models.Model):
    ticket_number = models.CharField(max_length=30, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=5000)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_tickets")
    category = models.ForeignKey("departments.Category", on_delete=models.PROTECT, related_name="tickets")
    department = models.ForeignKey("departments.Department", on_delete=models.PROTECT, related_name="tickets")
    building = models.CharField(max_length=100)
    floor = models.CharField(max_length=20, blank=True)
    room_or_area = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    resolution_note = models.TextField(blank=True)

    # SLA: deadlines are measured from sla_started_at (creation, or the latest reopening).
    sla_started_at = models.DateTimeField(default=timezone.now)
    response_due_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TicketQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="ticket_status_idx"),
            models.Index(fields=["priority"], name="ticket_priority_idx"),
            models.Index(fields=["created_at"], name="ticket_created_idx"),
            models.Index(fields=["department", "status"], name="ticket_dept_status_idx"),
            models.Index(fields=["reporter"], name="ticket_reporter_idx"),
        ]

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    def save(self, *args, **kwargs):
        if self._state.adding and not self.ticket_number:
            # Placeholder keeps the unique constraint satisfied; replaced by the
            # real number (derived from the primary key) in the same transaction.
            self.ticket_number = f"TMP-{uuid.uuid4().hex[:24]}"
            from django.db import transaction

            with transaction.atomic():
                super().save(*args, **kwargs)
                self.ticket_number = f"CF-{self.created_at.year}-{self.pk:06d}"
                Ticket.objects.filter(pk=self.pk).update(ticket_number=self.ticket_number)
            return
        super().save(*args, **kwargs)

    @property
    def current_assignment(self):
        cached = getattr(self, "active_assignments", None)
        if cached is not None:
            return cached[0] if cached else None
        return self.assignments.filter(is_active=True).select_related("assigned_to").first()

    @property
    def is_overdue(self) -> bool:
        if self.status in TERMINAL_STATUSES:
            return False
        now = timezone.now()
        if self.resolution_due_at and self.resolution_due_at < now:
            return True
        return bool(self.first_response_at is None and self.response_due_at and self.response_due_at < now)


class Assignment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="assignments")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments_received")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments_made")
    assignment_note = models.TextField(blank=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assigned_at", "-id"]
        constraints = [
            # At most one active assignment per ticket, enforced by PostgreSQL.
            models.UniqueConstraint(fields=["ticket"], condition=Q(is_active=True), name="one_active_assignment_per_ticket")
        ]

    def __str__(self):
        return f"{self.ticket.ticket_number} -> {self.assigned_to}"


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_comments")
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket.ticket_number}"


class TicketHistory(models.Model):
    class Event(models.TextChoices):
        CREATED = "CREATED", "Ticket created"
        STATUS = "STATUS", "Status changed"
        PRIORITY = "PRIORITY", "Priority changed"
        ASSIGNMENT = "ASSIGNMENT", "Assignment changed"
        DEADLINE = "DEADLINE", "Deadline changed"
        ATTACHMENT = "ATTACHMENT", "Attachment added"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_history")
    event_type = models.CharField(max_length=20, choices=Event.choices)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name_plural = "ticket history"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Ticket history is append-only and cannot be modified.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket.ticket_number}: {self.event_type}"


def attachment_upload_path(instance, filename):
    """Safe generated storage key; the user-supplied filename is never used on disk."""
    ext = getattr(instance, "_stored_ext", ".bin")
    return f"tickets/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}"


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_attachments")
    file = models.FileField(upload_to=attachment_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at", "id"]

    def __str__(self):
        return f"{self.original_filename} ({self.ticket.ticket_number})"
