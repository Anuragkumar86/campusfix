import django_filters
from django.db.models import Q

from .models import Priority, Status, Ticket


class TicketFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    status = django_filters.ChoiceFilter(choices=Status.choices)
    priority = django_filters.ChoiceFilter(choices=Priority.choices)
    category = django_filters.CharFilter(method="filter_category")
    building = django_filters.CharFilter(field_name="building", lookup_expr="icontains")
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    overdue = django_filters.BooleanFilter(method="filter_overdue")
    unassigned = django_filters.BooleanFilter(method="filter_unassigned")
    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("priority_rank", "priority"),
            ("resolution_due_at", "due_date"),
        )
    )

    class Meta:
        model = Ticket
        fields = ["search", "status", "priority", "category", "building", "overdue", "unassigned"]

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(Q(ticket_number__icontains=value) | Q(title__icontains=value) | Q(description__icontains=value))

    def filter_category(self, queryset, name, value):
        # numeric -> category id; otherwise case-insensitive name match ("network" matches "Network / Wi-Fi")
        value = value.strip()
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__name__icontains=value) if value else queryset

    def filter_overdue(self, queryset, name, value):
        return queryset.overdue() if value else queryset.exclude(pk__in=queryset.overdue().values("pk"))

    def filter_unassigned(self, queryset, name, value):
        # An assigned ticket is always ASSIGNED/IN_PROGRESS/...; OPEN and REOPENED mean "waiting for assignment".
        waiting = Q(status__in=[Status.OPEN, Status.REOPENED])
        return queryset.filter(waiting) if value else queryset.exclude(waiting)
