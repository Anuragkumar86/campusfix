from rest_framework import generics

from .models import Category, Department
from .serializers import CategorySerializer, DepartmentSerializer


class DepartmentListView(generics.ListAPIView):
    """Active departments (authenticated users only)."""

    serializer_class = DepartmentSerializer
    pagination_class = None
    queryset = Department.objects.filter(is_active=True)


class CategoryListView(generics.ListAPIView):
    """Active categories whose department is also active (what students may choose from)."""

    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(is_active=True, department__is_active=True).select_related("department")
