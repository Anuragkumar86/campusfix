from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """
    Django session auth (CSRF enforced on unsafe methods by DRF) that answers
    missing/expired sessions with 401 instead of 403, as the API contract states.
    """

    def authenticate_header(self, request):
        return "Session"
