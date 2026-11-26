"""Domain errors and the API error format: {"detail": "...", "code": "..."}."""
import logging

from django.db.utils import OperationalError
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

log = logging.getLogger("kti")


class DomainError(Exception):
    status_code = 400
    code = "invalid"

    def __init__(self, message: str, code: str = "", status_code: int = 0):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class Conflict(DomainError):
    status_code = 409
    code = "conflict"


def api_exception_handler(exc, context):
    if isinstance(exc, OperationalError):
        log.error("Database unavailable: %s", exc)
        return Response(
            {"detail": "Traffic data is temporarily unavailable. Please try again shortly.", "code": "unavailable"},
            status=503,
        )
    if isinstance(exc, DomainError):
        return Response({"detail": exc.message, "code": exc.code}, status=exc.status_code)
    response = drf_exception_handler(exc, context)
    if response is not None and isinstance(exc, Throttled):
        response.data = {
            "detail": "Too many requests from your device. Please wait a little before trying again.",
            "code": "throttled",
            "retry_after": int(exc.wait or 0),
        }
    return response
