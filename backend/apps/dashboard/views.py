from django.conf import settings
from django.db.models import Avg, Count, ExpressionWrapper, F, DurationField, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.departments.models import Department
from apps.tickets.models import ACTIVE_STATUSES, Priority, Status, Ticket
from apps.tickets.permissions import visible_tickets_for
from apps.tickets.serializers import TicketListSerializer


def _scoped(user):
    """Dashboards use the exact same scope as the ticket list (consistent numbers)."""
    return visible_tickets_for(user)


def _counts(queryset, field, choices):
    found = dict(queryset.values_list(field).annotate(n=Count("id")).order_by())
    return {value: found.get(value, 0) for value, _ in choices}


def _recent(queryset, request, limit=5):
    rows = queryset.select_related("category", "department", "reporter").order_by("-created_at")[:limit]
    return TicketListSerializer(rows, many=True, context={"request": request}).data


class SummaryView(APIView):
    """GET /api/dashboard/summary/ - role-scoped numbers computed with ORM aggregates."""

    def get(self, request):
        user = request.user
        qs = _scoped(user)
        data = {"role": user.role, "total": qs.count()}

        if user.role == Role.STUDENT:
            by_status = _counts(qs, "status", Status.choices)
            data.update(
                by_status=by_status,
                open_count=qs.filter(status__in=[Status.OPEN, Status.ASSIGNED, Status.REOPENED]).count(),
                in_progress=by_status[Status.IN_PROGRESS],
                resolved_or_closed=by_status[Status.RESOLVED] + by_status[Status.CLOSED],
                recent=_recent(qs, request),
            )
        elif user.role == Role.MAINTENANCE_STAFF:
            mine = qs.filter(assignments__assigned_to=user, assignments__is_active=True)
            soon = timezone.now() + timedelta(hours=settings.SLA_DUE_SOON_HOURS)
            active = mine.filter(status__in=ACTIVE_STATUSES)
            data.update(
                total=mine.count(),
                assigned=mine.filter(status=Status.ASSIGNED).count(),
                in_progress=mine.filter(status=Status.IN_PROGRESS).count(),
                overdue=active.overdue().count(),
                due_soon=active.filter(resolution_due_at__gte=timezone.now(), resolution_due_at__lte=soon).count(),
                due_soon_hours=settings.SLA_DUE_SOON_HOURS,
                recently_completed=_recent(mine.filter(status__in=[Status.RESOLVED, Status.CLOSED]).order_by("-resolved_at"), request),
                recent=_recent(active, request),
            )
        else:  # department manager or administrator
            avg = (
                qs.filter(resolved_at__isnull=False)
                .annotate(duration=ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField()))
                .aggregate(avg=Avg("duration"), n=Count("id"))
            )
            data.update(
                by_status=_counts(qs, "status", Status.choices),
                by_priority=_counts(qs, "priority", Priority.choices),
                unassigned=qs.filter(status__in=[Status.OPEN, Status.REOPENED]).count(),
                overdue=qs.overdue().count(),
                avg_resolution_hours=round(avg["avg"].total_seconds() / 3600, 1) if avg["avg"] else None,
                resolved_sample_size=avg["n"],
                department=(
                    {"id": user.department_id, "name": user.department.name}
                    if user.role == Role.DEPARTMENT_MANAGER and user.department_id else None
                ),
                recent=_recent(qs, request),
            )
            if user.is_admin_role:
                data["by_department"] = list(
                    Department.objects.annotate(
                        tickets_total=Count("tickets"),
                        tickets_open=Count("tickets", filter=Q(tickets__status__in=ACTIVE_STATUSES)),
                    ).values("id", "name", "tickets_total", "tickets_open")
                )
        return Response(data)


class CategoryCountsView(APIView):
    """GET /api/dashboard/categories/ - ticket counts per category (manager/admin)."""

    def get(self, request):
        if request.user.role not in (Role.DEPARTMENT_MANAGER, Role.ADMINISTRATOR) and not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to view this report.")
        rows = (
            _scoped(request.user).values("category_id", "category__name").annotate(count=Count("id")).order_by("-count", "category__name")
        )
        return Response([{"category_id": r["category_id"], "category": r["category__name"], "count": r["count"]} for r in rows])


class OverdueView(APIView):
    """GET /api/dashboard/overdue/ - overdue tickets in scope (staff: only their assigned work)."""

    def get(self, request):
        user = request.user
        if user.role == Role.STUDENT:
            raise PermissionDenied("You do not have permission to view this report.")
        qs = _scoped(user)
        if user.role == Role.MAINTENANCE_STAFF:
            qs = qs.filter(assignments__assigned_to=user, assignments__is_active=True)
        rows = qs.overdue().select_related("category", "department", "reporter").order_by("resolution_due_at")[:100]
        return Response({"count": len(rows), "results": TicketListSerializer(rows, many=True, context={"request": request}).data})
