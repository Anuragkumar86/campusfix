from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Role, User
from .serializers import CurrentUserSerializer, LoginSerializer, StaffBriefSerializer

INVALID_LOGIN = {"detail": "Invalid email or password."}


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """GET /api/auth/csrf/ - sets the csrftoken cookie and returns the token."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    """
    POST /api/auth/login/ - creates the Django session.
    CSRF is enforced explicitly (DRF only checks CSRF for already-authenticated users).
    The same generic message is returned for unknown accounts, wrong passwords
    and inactive accounts, so account existence is never revealed.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active:
            return Response(INVALID_LOGIN, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)  # rotates the session key and CSRF token
        return Response(CurrentUserSerializer(user).data)


class LogoutView(APIView):
    """POST /api/auth/logout/ - invalidates the session (CSRF enforced by DRF)."""

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ - source of truth for identity and role."""

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class EligibleStaffView(APIView):
    """
    GET /api/staff/eligible/ - active maintenance staff a manager may assign.
    Managers always get their own department; administrators may pass ?department=<id>.
    """

    def get(self, request):
        user = request.user
        queryset = User.objects.filter(role=Role.MAINTENANCE_STAFF, is_active=True)
        if user.role == Role.DEPARTMENT_MANAGER:
            if not user.department_id:
                return Response([])
            queryset = queryset.filter(department_id=user.department_id)
        elif user.is_admin_role:
            department = request.query_params.get("department")
            if department:
                if not department.isdigit():
                    return Response({"department": ["Must be a numeric id."]}, status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(department_id=int(department))
        else:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        return Response(StaffBriefSerializer(queryset.order_by("first_name", "email"), many=True).data)
