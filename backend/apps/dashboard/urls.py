from django.urls import path

from . import views

urlpatterns = [
    path("summary/", views.SummaryView.as_view(), name="dashboard-summary"),
    path("categories/", views.CategoryCountsView.as_view(), name="dashboard-categories"),
    path("overdue/", views.OverdueView.as_view(), name="dashboard-overdue"),
]
