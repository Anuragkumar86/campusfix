"""
Syllabus demo views (INT 253).
Unit II  : path()/re_path() URL mapping, URL parameters, HTTP responses, 404
Unit III : templates, DTL, inheritance
Unit IV  : forms, GET/POST, CSRF, Post/Redirect/Get
Unit VI  : cookies, sessions, login/logout
"""
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.tickets.models import Ticket

from .forms import BuildingPreferenceForm, DemoFeedbackForm

SAMPLE_ISSUES = [
    {"title": "Projector flickering", "building": "Block-A", "status": "OPEN", "urgent": False},
    {"title": "Wi-Fi down on 2nd floor", "building": "Library", "status": "IN_PROGRESS", "urgent": True},
    {"title": "Water leakage in washroom", "building": "Hostel-1", "status": "RESOLVED", "urgent": True},
]


def index(request):
    """Unit III: template context with variables, loops, conditions, {% empty %}."""
    context = {
        "issues": SAMPLE_ISSUES,
        "no_issues": [],  # demonstrates {% empty %}
        "building": request.COOKIES.get("preferred_building"),
        "ticket_count": Ticket.objects.count(),
    }
    return render(request, "django_demo/index.html", context)


def building_detail(request, name):
    """Unit II: URL parameter with path() converter (<str:name>)."""
    issues = [i for i in SAMPLE_ISSUES if i["building"].lower() == name.lower()]
    return render(request, "django_demo/building.html", {"name": name, "issues": issues})


def ticket_reference(request, year, number):
    """Unit II: re_path() with named regular-expression groups, e.g. /demo/ref/2026/000001/"""
    reference = f"CF-{year}-{number}"
    ticket = Ticket.objects.filter(ticket_number=reference).first()
    if ticket is None and not re.fullmatch(r"\d{6}", number):
        raise Http404("Malformed reference")
    return render(request, "django_demo/reference.html", {"reference": reference, "year": year, "number": number, "found": ticket is not None})


@require_http_methods(["GET", "POST"])
def feedback(request):
    """Unit IV: GET shows the form, POST validates it, success redirects (PRG)."""
    if request.method == "POST":
        form = DemoFeedbackForm(request.POST)
        if form.is_valid():
            submissions = request.session.get("demo_feedback", [])
            submissions.append({k: v for k, v in form.cleaned_data.items()})
            request.session["demo_feedback"] = submissions[-5:]
            messages.success(request, "Thanks! Your demo feedback was recorded in your session.")
            return redirect("django_demo:feedback_done")  # Post/Redirect/Get
    else:
        form = DemoFeedbackForm()
    return render(request, "django_demo/feedback.html", {"form": form})


def feedback_done(request):
    return render(request, "django_demo/feedback_done.html", {"submissions": request.session.get("demo_feedback", [])})


def session_page(request):
    """Unit VI: session-backed page (visit counter stored server-side)."""
    request.session["visits"] = request.session.get("visits", 0) + 1
    return render(request, "django_demo/session.html", {"visits": request.session["visits"]})


@require_http_methods(["GET", "POST"])
def cookie_page(request):
    """Unit VI: a simple cookie remembering the preferred building."""
    if request.method == "POST":
        form = BuildingPreferenceForm(request.POST)
        if form.is_valid():
            response = redirect("django_demo:cookie")
            response.set_cookie("preferred_building", form.cleaned_data["building"], max_age=30 * 24 * 3600, samesite="Lax", httponly=True)
            return response
    else:
        form = BuildingPreferenceForm()
    return render(request, "django_demo/cookie.html", {"form": form, "building": request.COOKIES.get("preferred_building")})


@require_http_methods(["POST"])
def clear_cookie(request):
    response = redirect("django_demo:cookie")
    response.delete_cookie("preferred_building")
    return response


@login_required
def secret(request):
    """Unit VI: page protected by authentication (redirects anonymous users to the demo login)."""
    return render(request, "django_demo/secret.html")
