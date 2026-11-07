import logging

from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """Consistent JSON errors; never leaks stack traces or database details."""
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "This record is referenced by other records and cannot be deleted."},
            status=status.HTTP_409_CONFLICT,
        )
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        return Response({"detail": "A server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response
