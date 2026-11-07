from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import EligibleStaffView
from config import views

handler404 = "config.views.not_found"
handler500 = "config.views.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", views.health, name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/staff/eligible/", EligibleStaffView.as_view(), name="staff-eligible"),
    path("api/tickets/", include("apps.tickets.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/", include("apps.departments.urls")),
    path("demo/", include("apps.django_demo.urls")),
]
