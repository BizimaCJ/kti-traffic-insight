from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit import services as audit
from apps.audit.models import AuditAction
from apps.core.permissions import IsAdministrator
from apps.core.throttles import LoginThrottle


def _user_payload(user) -> dict:
    return {"username": user.username, "full_name": user.get_full_name() or user.username}


def _enforce_csrf(request):
    """Login and logout must carry the CSRF token too (the session endpoint sets the cookie)."""
    SessionAuthentication().enforce_csrf(request)


class SessionView(APIView):
    """Who is logged in? Also sets the CSRF cookie that the front end sends back."""

    def get(self, request):
        get_token(request._request)
        user = request.user
        is_admin = bool(user and user.is_authenticated and user.is_staff and user.is_active)
        return Response({
            "authenticated": is_admin,
            "user": _user_payload(user) if is_admin else None,
            "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
        })


class LoginView(APIView):
    """Administrator login (FR 12)."""

    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        _enforce_csrf(request)
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        user = authenticate(request._request, username=username, password=password)
        if user is None or not user.is_staff or not user.is_active:
            return Response({"detail": "Incorrect username or password.", "code": "bad_credentials"}, status=400)
        with transaction.atomic():
            login(request._request, user)
            audit.record(user, AuditAction.LOGIN, "User", user.pk)
        return Response({"authenticated": True, "user": _user_payload(user),
                         "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES})


class LogoutView(APIView):
    """Administrator logout (FR 13)."""

    permission_classes = [IsAdministrator]

    def post(self, request):
        with transaction.atomic():
            audit.record(request.user, AuditAction.LOGOUT, "User", request.user.pk)
        logout(request._request)
        return Response({"authenticated": False})
