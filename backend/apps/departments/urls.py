from django.urls import path

from . import views

urlpatterns = [
    path("departments/", views.DepartmentListView.as_view(), name="department-list"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
]
