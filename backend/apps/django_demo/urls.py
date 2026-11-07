from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from . import views

app_name = "django_demo"

urlpatterns = [
    path("", views.index, name="index"),
    path("building/<str:name>/", views.building_detail, name="building"),
    # re_path with named groups: year 20xx and a 6-digit sequence number
    re_path(r"^ref/(?P<year>20\d{2})/(?P<number>\d{6})/$", views.ticket_reference, name="reference"),
    path("feedback/", views.feedback, name="feedback"),
    path("feedback/done/", views.feedback_done, name="feedback_done"),
    path("session/", views.session_page, name="session"),
    path("cookie/", views.cookie_page, name="cookie"),
    path("cookie/clear/", views.clear_cookie, name="cookie_clear"),
    path("secret/", views.secret, name="secret"),
    path("login/", auth_views.LoginView.as_view(template_name="django_demo/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
