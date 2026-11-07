from django.db.models import Case, IntegerField, Prefetch, Value, When
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from . import permissions as perms
from . import services
from .filters import TicketFilter
from .models import Assignment, Attachment, Ticket
from .pagination import StandardPagination
from .serializers import (
    AssignmentCreateSerializer, AttachmentSerializer, AttachmentUploadSerializer,
    CommentCreateSerializer, CommentSerializer, HistorySerializer, PriorityChangeSerializer,
    StatusChangeSerializer, TicketCreateSerializer, TicketDetailSerializer,
    TicketListSerializer, TicketUpdateSerializer,
)

PRIORITY_RANK = Case(
    When(priority="LOW", then=Value(1)),
    When(priority="MEDIUM", then=Value(2)),
    When(priority="HIGH", then=Value(3)),
    When(priority="URGENT", then=Value(4)),
    output_field=IntegerField(),
)


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/tickets/ ... Every query starts from ``visible_tickets_for(user)``, so a
    ticket outside the caller's scope is simply a 404 on every sub-resource too.
    """

    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TicketFilter
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "head", "options"]  # no PUT / DELETE

    def get_queryset(self):
        active = Assignment.objects.filter(is_active=True).select_related("assigned_to")
        return (
            perms.visible_tickets_for(self.request.user)
            .select_related("category", "department", "reporter")
            .prefetch_related(Prefetch("assignments", queryset=active, to_attr="active_assignments"))
            .annotate(priority_rank=PRIORITY_RANK)
        )

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "create":
            return TicketCreateSerializer
        if self.action == "partial_update":
            return TicketUpdateSerializer
        return TicketDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permission() for permission in self.permission_classes] + [perms.CanCreateTicket()]
        return super().get_permissions()

    def _detail_response(self, ticket_id, request, code=status.HTTP_200_OK):
        ticket = self.get_queryset().get(pk=ticket_id)
        return Response(TicketDetailSerializer(ticket, context={"request": request}).data, status=code)

    # --- create / update -------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = TicketCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ticket = services.create_ticket(
            reporter=request.user,
            category=data["category"],
            title=data["title"],
            description=data["description"],
            building=data["building"],
            floor=data.get("floor", ""),
            room_or_area=data.get("room_or_area", ""),
            image=data.get("image"),
        )
        return self._detail_response(ticket.pk, request, status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not perms.can_edit_basic_fields(request.user, ticket):
            raise PermissionDenied("You cannot edit this ticket.")
        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._detail_response(ticket.pk, request)

    # --- read-only sub-resources ----------------------------------------
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        ticket = self.get_object()
        internal = bool(perms.roles_for(request.user, ticket) & {perms.MANAGER, perms.ADMIN, perms.ASSIGNEE})
        data = HistorySerializer(ticket.history.select_related("changed_by"), many=True, context={"can_see_internal": internal}).data
        return Response(data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        ticket = self.get_object()
        if request.method == "GET":
            return Response(CommentSerializer(ticket.comments.select_related("author"), many=True).data)
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = services.add_comment(ticket_id=ticket.pk, actor=request.user, message=serializer.validated_data["message"])
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="attachments")
    def attachments(self, request, pk=None):
        ticket = self.get_object()
        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = services.add_attachment(ticket_id=ticket.pk, actor=request.user, upload=serializer.validated_data["file"])
        return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path=r"attachments/(?P<attachment_id>\d+)")
    def attachment_download(self, request, pk=None, attachment_id=None):
        ticket = self.get_object()  # 404 unless the user may view the ticket
        try:
            attachment = ticket.attachments.get(pk=attachment_id)
            handle = attachment.file.open("rb")
        except (Attachment.DoesNotExist, FileNotFoundError, ValueError):
            raise NotFound()
        response = FileResponse(handle, content_type=attachment.content_type)
        response["Content-Disposition"] = 'inline; filename="attachment"'
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, max-age=0"
        return response

    # --- explicit action endpoints --------------------------------------
    @action(detail=True, methods=["post"])
    def assignments(self, request, pk=None):
        ticket = self.get_object()
        serializer = AssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.assign_ticket(
            ticket_id=ticket.pk, actor=request.user,
            assignee_id=serializer.validated_data["assigned_to"], note=serializer.validated_data["note"],
        )
        return self._detail_response(ticket.pk, request, status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_status(
            ticket_id=ticket.pk, actor=request.user,
            new_status=serializer.validated_data["status"], note=serializer.validated_data["note"],
        )
        return self._detail_response(ticket.pk, request)

    @action(detail=True, methods=["post"], url_path="priority")
    def change_priority(self, request, pk=None):
        ticket = self.get_object()
        serializer = PriorityChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_priority(
            ticket_id=ticket.pk, actor=request.user,
            priority=serializer.validated_data["priority"], note=serializer.validated_data["note"],
        )
        return self._detail_response(ticket.pk, request)
