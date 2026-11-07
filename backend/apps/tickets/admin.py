from django.contrib import admin

from .models import Assignment, Attachment, Comment, Ticket, TicketHistory


class ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AssignmentInline(ReadOnlyInline):
    model = Assignment
    fields = ("assigned_to", "assigned_by", "assigned_at", "is_active", "unassigned_at", "assignment_note")


class CommentInline(ReadOnlyInline):
    model = Comment
    fields = ("author", "message", "created_at")


class HistoryInline(ReadOnlyInline):
    model = TicketHistory
    fields = ("created_at", "changed_by", "event_type", "old_value", "new_value", "note")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "title", "status", "priority", "department", "reporter", "created_at")
    list_filter = ("status", "priority", "department", "category")
    search_fields = ("ticket_number", "title", "description", "reporter__email")
    date_hierarchy = "created_at"
    readonly_fields = ("ticket_number", "reporter", "category", "department", "created_at", "updated_at", "sla_started_at")
    inlines = [AssignmentInline, CommentInline, HistoryInline]

    def has_delete_permission(self, request, obj=None):
        return False  # historical records are not hard-deleted

    def has_add_permission(self, request):
        return False  # tickets are created through the API (reporter/department rules)

    def save_model(self, request, obj, form, change):
        # Keep the audit trail honest when an administrator edits status/priority here.
        if change:
            old = Ticket.objects.get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if old.status != obj.status:
                TicketHistory.objects.create(ticket=obj, changed_by=request.user, event_type="STATUS", old_value=old.status, new_value=obj.status, note="Changed in Django Admin.")
            if old.priority != obj.priority:
                TicketHistory.objects.create(ticket=obj, changed_by=request.user, event_type="PRIORITY", old_value=old.priority, new_value=obj.priority, note="Changed in Django Admin.")
        else:
            super().save_model(request, obj, form, change)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ("ticket", "event_type", "old_value", "new_value", "changed_by", "created_at")
    list_filter = ("event_type",)
    search_fields = ("ticket__ticket_number",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "assigned_to", "assigned_by", "is_active", "assigned_at")
    list_filter = ("is_active",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("message", "ticket__ticket_number")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "ticket", "uploaded_by", "content_type", "file_size", "uploaded_at")
