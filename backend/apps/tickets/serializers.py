from rest_framework import serializers

from apps.accounts.models import User
from apps.departments.models import Category

from . import permissions as perms
from .models import Assignment, Attachment, Comment, Priority, Status, Ticket, TicketHistory
from .validators import validate_image_upload


class UserBriefSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="display_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "role"]


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    uploaded_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = Attachment
        fields = ["id", "original_filename", "content_type", "file_size", "uploaded_by", "uploaded_at", "url"]

    def get_url(self, obj):
        # Permission-checked download endpoint (media files are never public).
        return f"/api/tickets/{obj.ticket_id}/attachments/{obj.id}/"


class CommentSerializer(serializers.ModelSerializer):
    author = UserBriefSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "message", "created_at"]


class CommentCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)


class HistorySerializer(serializers.ModelSerializer):
    changed_by = UserBriefSerializer(read_only=True)
    event_label = serializers.CharField(source="get_event_type_display", read_only=True)
    note = serializers.SerializerMethodField()

    class Meta:
        model = TicketHistory
        fields = ["id", "event_type", "event_label", "old_value", "new_value", "note", "changed_by", "created_at"]

    def get_note(self, obj):
        # Assignment notes are manager -> staff instructions; hide them from reporter-only viewers.
        if obj.event_type == TicketHistory.Event.ASSIGNMENT and not self.context.get("can_see_internal", True):
            return ""
        return obj.note


class AssignmentSerializer(serializers.ModelSerializer):
    assigned_to = UserBriefSerializer(read_only=True)
    assigned_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = Assignment
        fields = ["id", "assigned_to", "assigned_by", "assignment_note", "assigned_at", "is_active", "unassigned_at"]


class TicketListSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    category = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    reporter = UserBriefSerializer(read_only=True)
    assigned_to = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "ticket_number", "title", "status", "status_label", "priority", "priority_label",
            "category", "department", "building", "floor", "room_or_area", "reporter", "assigned_to",
            "response_due_at", "resolution_due_at", "is_overdue", "created_at", "updated_at",
        ]

    def get_category(self, obj):
        return {"id": obj.category_id, "name": obj.category.name}

    def get_department(self, obj):
        return {"id": obj.department_id, "name": obj.department.name}

    def get_assigned_to(self, obj):
        assignment = obj.current_assignment
        return UserBriefSerializer(assignment.assigned_to).data if assignment else None


class TicketDetailSerializer(TicketListSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    history = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + [
            "description", "resolution_note", "first_response_at", "resolved_at", "closed_at",
            "attachments", "comments", "history", "assignments", "permissions",
        ]

    def _roles(self, obj):
        return perms.roles_for(self.context["request"].user, obj)

    def get_history(self, obj):
        internal = bool(self._roles(obj) & {perms.MANAGER, perms.ADMIN, perms.ASSIGNEE})
        return HistorySerializer(obj.history.select_related("changed_by"), many=True, context={"can_see_internal": internal}).data

    def get_assignments(self, obj):
        # Full assignment trail is for managers/administrators only.
        if self._roles(obj) & {perms.MANAGER, perms.ADMIN}:
            return AssignmentSerializer(obj.assignments.select_related("assigned_to", "assigned_by"), many=True).data
        return []

    def get_permissions(self, obj):
        return perms.ticket_permissions(self.context["request"].user, obj)


class TicketCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=5000)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True, department__is_active=True).select_related("department"),
        error_messages={"does_not_exist": "Select an active category.", "incorrect_type": "Select an active category."},
    )
    building = serializers.CharField(max_length=100)
    floor = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    room_or_area = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    image = serializers.FileField(required=False, allow_null=True)

    def validate_image(self, value):
        if value:
            validate_image_upload(value)
        return value


class TicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["title", "description", "building", "floor", "room_or_area"]
        extra_kwargs = {"floor": {"required": False}, "room_or_area": {"required": False}}


class AssignmentCreateSerializer(serializers.Serializer):
    assigned_to = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")


class StatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Status.values)
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000, default="")


class PriorityChangeSerializer(serializers.Serializer):
    priority = serializers.ChoiceField(choices=Priority.values)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        validate_image_upload(value)
        return value
